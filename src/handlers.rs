use actix_web::http::header::{ContentDisposition, DispositionType};
use actix_web::{get, post, web, Error, HttpRequest, HttpResponse, Responder};
use chrono::{DateTime, Datelike, Utc};
use dotenv::dotenv;
use ignore::WalkBuilder;
use lettre::transport::smtp::authentication::Credentials;
use lettre::{Message, SmtpTransport, Transport};
use serde::Deserialize;
use std::collections::HashSet;
use std::time::SystemTime;
use whatlang::{Detector, Lang};

use crate::metadata::Metadata;

const SPAM_SHARDS: &[&str] = &[
    "we have a promotional offer",
    "you are receiving this message",
    "http://",
    "https://",
    "whatsapp",
];

const SPAM_CHAR: usize = 50;

#[derive(Debug, Deserialize)]
pub struct Tag {
    tag: Option<String>,
}

#[get("/colophon")]
pub async fn colophon(templates: web::Data<tera::Tera>) -> impl Responder {
    let context = tera::Context::new();
    match templates.render("colophon.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong!</p>")
        }
    }
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
        None => None,
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
    println!("{:?}", &metadata);

    context.insert("metadata", &metadata);
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
pub async fn serve_static(
    path: web::Path<(String, String)>,
) -> Result<actix_files::NamedFile, Error> {
    let (slug, file_path) = path.into_inner();
    let file =
        actix_files::NamedFile::open(format!("./assets/posts/{}/static/{}", slug, file_path))?;
    Ok(file
        .use_last_modified(true)
        .set_content_disposition(ContentDisposition {
            disposition: DispositionType::Attachment,
            parameters: vec![],
        }))
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

fn pull_metadatas(tag: Option<&String>) -> Result<Vec<(i32, Vec<Metadata>)>, std::io::Error> {
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

    metadatas.sort_by(|a, b| {
        b.string_date_to_datetime("date")
            .cmp(&a.string_date_to_datetime("date"))
    });

    let post_years: HashSet<i32> = metadatas
        .clone()
        .iter()
        .map(|m| m.string_date_to_datetime("date").year())
        .collect();

    let mut mapped_posts: Vec<(i32, Vec<Metadata>)> = post_years
        .into_iter()
        .map(|y| {
            (
                y,
                metadatas
                    .clone()
                    .into_iter()
                    .filter(|m| m.string_date_to_datetime("date").year() == y)
                    .collect::<Vec<Metadata>>(),
            )
        })
        .collect();
    mapped_posts.sort_by(|a, b| b.0.cmp(&a.0));

    Ok(mapped_posts)
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
