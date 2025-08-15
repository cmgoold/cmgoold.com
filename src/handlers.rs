use actix_web::{get, post, web, Error, HttpResponse, HttpRequest, Responder};
use actix_web::http::header::{ContentDisposition, DispositionType};
use ignore::WalkBuilder;
use std::time::SystemTime;
use chrono::{DateTime, Utc};
use serde::Deserialize;
use lettre::{Message, SmtpTransport, Transport};
use lettre::transport::smtp::authentication::Credentials;
use dotenv::dotenv;
use whatlang::{Lang, Detector};

use crate::metadata::Metadata;
use crate::contact::ContactForm;

const SPAM_SHARDS: &[&str] = &[
    "we have a promotional offer",
    "you are receiving this message",
];

#[derive(Debug, Deserialize)]
pub struct Tag {
    tag: Option<String>
}

#[get("/")]
pub async fn index(templates: web::Data<tera::Tera>) -> impl Responder {
    let mut context = tera::Context::new();
    context.insert("file", "");

    match templates.render("index.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong!</p>")
        }
    }
}

#[get("/posts")]
pub async fn posts(templates: web::Data<tera::Tera>, request: HttpRequest) -> impl Responder {
    let mut context = tera::Context::new();
    context.insert("file", "");

    let query = web::Query::<Tag>::from_query(request.query_string()).unwrap();
    let tag = match &query.tag {
        Some(s) => Some(s),
        None => None
    };

    let metadata = match pull_metadatas(tag) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong</p>");
        }
    };

    let datetimes: Vec<_> = metadata.iter()
        .map(|m| m.string_date_to_datetime("date"))
        .collect();

    context.insert("metadata", &metadata);
    context.insert("datetimes", &datetimes);
    context.insert("tag", &tag);

    match templates.render("posts.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong!</p>")
        }
    }
}

#[get("/posts/{slug}/static/{file_path}")]
pub async fn serve_static(path: web::Path<(String, String)>) ->  Result<actix_files::NamedFile, Error> {
    let (slug, file_path) = path.into_inner();
    let file = actix_files::NamedFile::open(format!("./assets/posts/{}/static/{}", slug, file_path))?;
    Ok(file
        .use_last_modified(true)
        .set_content_disposition(ContentDisposition {
            disposition: DispositionType::Attachment,
            parameters: vec![],
        })
    )
}

#[get("/posts/{slug}")]
pub async fn post(templates: web::Data<tera::Tera>, slug: web::Path<String>) -> impl Responder {
    let mut context = tera::Context::new();
    context.insert("file", "post");

    let post: String = match pull_post(&slug) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::NotFound()
                .content_type("text/html")
                .body("<p>Could not find the post</p>");
        }
    };

    let metadata: Metadata = match pull_metadata(&slug) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::NotFound()
                .content_type("text/html")
                .body("<p>Could not find the metadata</p>");
        }
    };

    context.insert("post", &post);
    let posted = &metadata.string_date_to_datetime("date");
    let edited = &metadata.string_date_to_datetime("edited");
    let future_edits = edited > posted;
    context.insert("posted", &posted);
    context.insert("edited", &edited);
    context.insert("future_edits", &future_edits);
    context.insert("metadata", &metadata);

    match templates.render("post.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::NotFound()
                .content_type("text/html")
                .body("<p>Could not find post</p>");
        }
    }
}

#[get("/contact")]
pub async fn contact(templates: web::Data<tera::Tera>) -> impl Responder {
    let mut context = tera::Context::new();
    context.insert("file", "");

    match templates.render("contact.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong!</p>")
        }
    }
}

#[post("/contact")]
pub async fn send(templates: web::Data<tera::Tera>, form: web::Form<ContactForm>) -> impl Responder {
    let mut context = tera::Context::new();
    context.insert("file", "");

    let submitted = true;
    context.insert("submitted", &submitted);
    context.insert("name", &form.name);

    let name = form.name.to_owned();
    let from_email = form.email.to_owned();
    let from = format!("{name} <{from_email}>");

    dotenv().ok();
    let to = std::env::var("FORWARDING_EMAIL")
        .ok()
        .unwrap_or(String::from(""));
    println!("To address set to {}", to);

    let username = std::env::var("USERNAME").ok().unwrap_or(String::from(""));
    let password = std::env::var("PASSWORD").ok().unwrap_or(String::from(""));

    if from_email.is_empty() || !from_email.contains("@") {
        return HttpResponse::InternalServerError()
            .content_type("text/html")
            .body("<p>Error! Did you provide a valid email address?</p>");
    }
    if is_spam(&form) {
        return HttpResponse::InternalServerError()
            .content_type("text/html")
            .body("<p>Oops! Your message wasn't long enough, contained suspicious language indicative of spam, or wasn't written in English. Try again.")
    }

    let subject = format!("New website contact received from {from}");
    let creds = Credentials::new(username.to_owned(), password.to_owned());

    let email = Message::builder()
        .from(String::from(from).parse().unwrap())
        .to(to.parse().unwrap())
        .subject(subject)
        .body(String::from(&form.message))
        .unwrap();

    let mailer = SmtpTransport::starttls_relay("smtp.gmail.com")
        .unwrap()
        .credentials(creds)
        .build();

    match mailer.send(&email) {
        Ok(_) => println!("Email sent succesffully!"),
        Err(e) => panic!("Could not send email: {e:?}"),
    };

    match templates.render("contact.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong!</p>")
        }
    }
}

fn is_spam(form: &web::Form<ContactForm>) -> bool {
    let allowed = std::vec![Lang::Eng];
    let detector = Detector::with_allowlist(allowed);
    let lang = detector.detect_lang(&form.message);
    let is_english: bool = lang == Some(Lang::Eng);

    return form.message.is_empty() || 
        form.message.chars().count() < 20 ||
        !is_english ||
        SPAM_SHARDS.iter().any(|&shard| 
            form.message.to_lowercase().contains(shard)
        );
}

fn pull_metadatas(tag: Option<&String>) -> Result<Vec<Metadata>, std::io::Error> {
    let mut t = ignore::types::TypesBuilder::new();
    t.add_defaults();
    let tomls = match t.select("toml").build() {
        Ok(t) => t,
        Err(e) => {
            println!("{:}", e);
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "could not build Markdown file type matcher",
            ));
        }
    };

    let file_walker = WalkBuilder::new("./assets/posts/").types(tomls).build();

    let mut metadatas = Vec::new();
    for meta in file_walker {
        match meta {
            Ok(m) => {
                if m.path().is_file() && m.path().to_str().unwrap().contains("metadata") {
                    let content = std::fs::read_to_string(m.path())?;
                    let metadata: Metadata = match toml::from_str(&content) {
                        Ok(s) => s,
                        Err(e) => {
                            println!("{:}", e);
                            return Err(std::io::Error::new(
                                std::io::ErrorKind::NotFound,
                                "could not parse metadata content",
                            ));
                        }
                    };
                    if metadata.publish {
                        if !tag.is_some() {
                            metadatas.push(metadata);
                        } else {
                            if metadata.tags.contains(tag.unwrap()) {
                                metadatas.push(metadata);
                            }
                        }
                    }
                }
            }
            Err(e) => {
                println!("{:}", e);
                return Err(std::io::Error::new(
                    std::io::ErrorKind::NotFound,
                    "could not find Markdown file",
                ));
            }
        }
    }

    metadatas.sort_by(|a, b| b.string_date_to_datetime("date").cmp(&a.string_date_to_datetime("date")));

    Ok(metadatas)
}

fn pull_post(slug: &str) -> Result<String, std::io::Error> {
    let content = match std::fs::read_to_string(format!("./assets/posts/{}/post.html", slug)) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return Err(e);
        }
    };

    Ok(content)
}

fn pull_metadata(slug: &str) -> Result<Metadata, std::io::Error> {
    let metadata_path = format!("./assets/posts/{}/metadata.toml", slug);
    let post_path_string = format!("./assets/posts/{}/post.html", slug);
    let post_path = std::path::Path::new(&post_path_string);
    let raw = std::fs::read_to_string(metadata_path)?;
    let edited_date_systime: SystemTime = post_path.metadata().unwrap().modified().unwrap();
    let edited_datetime: DateTime<Utc> = edited_date_systime.into();

    let mut metadata: Metadata = match toml::from_str(&raw) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "could not parse metadata",
            ));
        }
    };
    metadata.edited_date = Some(edited_datetime.format("%Y-%m-%d").to_string());

    Ok(metadata)
}
