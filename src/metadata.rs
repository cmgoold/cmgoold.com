use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct Metadata {
    title: String,
    date: String,
    slug: String,
    tags: Vec<String>,
}
