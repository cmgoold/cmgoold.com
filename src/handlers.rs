use actix_web::{get, web, HttpResponse, Responder};
use pulldown_cmark::{Parser, Options, html};
use ignore::WalkBuilder;

use crate::metadata::Metadata;

#[get("/")]
pub async fn index(templates: web::Data<tera::Tera>) -> impl Responder {
    let context = tera::Context::new();

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
pub async fn posts(templates: web::Data<tera::Tera>) -> impl Responder {
    let mut context = tera::Context::new();

    let metadata = match pull_metadata() {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::InternalServerError()
                .content_type("text/html")
                .body("<p>Something went wrong</p>");
            }
    };
    
    context.insert("metadata", &metadata);

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

    let post: String = match pull_post(&slug) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::NotFound()
                .content_type("text/html")
                .body("<p>Could not find the post</p>")
        }
    };

    let options = Options::empty();
    let parser = Parser::new_ext(&post, options);

    let mut output = String::new();
    html::push_html(&mut output, parser);

    context.insert("post", &output);

    match templates.render("post.html", &context) {
        Ok(s) => HttpResponse::Ok().content_type("text/html").body(s),
        Err(e) => {
            println!("{:?}", e);
            return HttpResponse::NotFound()
                .content_type("text/html")
                .body("<p>Could not find post</p>")
        }
    }
}

fn pull_metadata() -> Result<Vec<Metadata>, std::io::Error> {
    let mut t = ignore::types::TypesBuilder::new();
    t.add_defaults();
    let tomls = match t.select("toml").build() {
        Ok(t) => t,
        Err(e) => {
            println!("{:}", e);
            return Err(std::io::Error::new(std::io::ErrorKind::Other,
                    "could not build Markdown file type matcher"
            ))
        }
    };

    let file_walker = WalkBuilder::new("./_assets/posts/").types(tomls).build();

    let mut metadatas = Vec::new();
    for meta in file_walker {
        match meta {
            Ok(m) => {
                if m.path().is_file() {
                    let content = std::fs::read_to_string(m.path())?;
                    let metadata: Metadata = match toml::from_str(&content) {
                        Ok(s) => s,
                        Err(e) => {
                            println!("{:}", e);
                            return Err(
                                std::io::Error::new(std::io::ErrorKind::NotFound,
                                    "could not parse metadata content"
                                ))
                        }
                    };
                    metadatas.push(metadata);
                }
            }
            Err(e) => {
                println!("{:}", e);
                return Err(std::io::Error::new(std::io::ErrorKind::NotFound,
                        "could not find Markdown file"
                ));
            }
        }
    }

    Ok(metadatas)
}

fn pull_post(slug: &str) -> Result<String, std::io::Error> {
    let content = match std::fs::read_to_string(format!("./_assets/posts/{}/post.md", slug)) {
        Ok(s) => s,
        Err(e) => {
            println!("{:?}", e);
            return Err(e)
        }
    };

    Ok(content)
}
