use actix_web::{dev::Server, web, get, App, HttpServer, HttpResponse, Responder};
use tera::Tera;

mod handlers;

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
        tera.autoescape_on(vec![".html", ".sqp"]);
        tera
    };
}


pub fn serve() -> Result<Server, std::io::Error> {
    let server = HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(TEMPLATES.clone()))
            .route("/status", web::get().to(HttpResponse::Ok))
            .service(handlers::index)
    })
    .bind(("127.0.0.1", 8080))?
    .run();

    Ok(server)
}
