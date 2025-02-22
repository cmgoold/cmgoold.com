use serde::Deserialize;

#[derive(Deserialize)]
pub struct ContactForm {
    pub name: String,
    pub email: String,
    pub message: String,
}
