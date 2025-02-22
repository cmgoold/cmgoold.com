use actix_files::Files;
use actix_web::{dev::Server, web, App, HttpResponse, HttpServer};
use tera::Tera;

mod handlers;
mod metadata;
mod contact;

#[macro_use]
extern crate lazy_static;

lazy_static! {
    pub static ref TEMPLATES: Tera = {
        let mut templates = match Tera::new("assets/templates/**/*.html") {
            Ok(t) => t,
            Err(e) => {
                println!("Parsing error(s): {}", e);
                ::std::process::exit(1);
            }
        };
        templates.autoescape_on(vec![".html"]);
        templates
    };
}

pub fn serve() -> Result<Server, std::io::Error> {
    let server = HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(TEMPLATES.clone()))
            .service(Files::new("/styles", "./assets/styles/").use_last_modified(true))
            .route("/status", web::get().to(HttpResponse::Ok))
            .service(handlers::index)
            .service(handlers::posts)
            .service(handlers::post)
            .service(handlers::serve_static)
            .service(handlers::contact)
            .service(handlers::send)
    })
    .bind(("0.0.0.0", 8080))?
    .run();

    Ok(server)
}
