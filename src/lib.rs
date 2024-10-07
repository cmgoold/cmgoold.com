use actix_files::Files;
use actix_web::{dev::Server, web, App, HttpResponse, HttpServer};
use tera::Tera;

mod handlers;
mod metadata;

#[macro_use]
extern crate lazy_static;

lazy_static! {
    pub static ref TEMPLATES: Tera = {
        let mut tera = match Tera::new("_assets/templates/**/*.html") {
            Ok(t) => t,
            Err(e) => {
                println!("Parsing error(s): {}", e);
                ::std::process::exit(1);
            }
        };
        tera.autoescape_on(vec![".html", ".sql"]);
        tera
    };
}

pub fn serve() -> Result<Server, std::io::Error> {
    let server = HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(TEMPLATES.clone()))
            .service(Files::new("/styles", "_assets/styles/").use_last_modified(true))
            .route("/status", web::get().to(HttpResponse::Ok))
            .service(handlers::index)
            .service(handlers::posts)
            .service(handlers::post)
    })
    .bind(("127.0.0.1", 8080))?
    .run();

    Ok(server)
}
