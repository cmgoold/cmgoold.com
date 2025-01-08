use cmgoold::serve;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    serve()?.await?;
    Ok(())
}
