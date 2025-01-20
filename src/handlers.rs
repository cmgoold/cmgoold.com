use actix_web::{get, web, HttpResponse, HttpRequest, Responder};
use ignore::WalkBuilder;
use pulldown_cmark::{html, Options, Parser};
use std::time::SystemTime;
use chrono::{DateTime, Utc};
use serde::Deserialize;

use crate::metadata::Metadata;

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

    let mut options = Options::empty();
    options.insert(Options::ENABLE_MATH);
    options.insert(Options::ENABLE_YAML_STYLE_METADATA_BLOCKS);
    let parser = Parser::new_ext(&post, options);

    let mut output = String::new();
    html::push_html(&mut output, parser);

    context.insert("post", &output);
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

    metadatas.sort_by(|a, b| b.string_date_to_datetime().cmp(&a.string_date_to_datetime()));

    Ok(metadatas)
}

fn pull_post(slug: &str) -> Result<String, std::io::Error> {
    let content = match std::fs::read_to_string(format!("./assets/posts/{}/post.md", slug)) {
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
    let post_path_string = format!("./assets/posts/{}/post.md", slug);
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
