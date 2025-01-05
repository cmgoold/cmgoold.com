use serde::{Deserialize, Serialize};
use chrono::{NaiveDate};

#[derive(Serialize, Deserialize, Debug)]
pub struct Metadata {
    title: String,
    pub date: String,
    pub edited_date: Option<String>,
    slug: String,
    pub tags: Vec<String>,
    pub publish: bool,
    pub edit_notes: Option<String>,
}

impl Metadata {
    pub fn string_date_to_datetime(&self) -> NaiveDate {
        NaiveDate::parse_from_str(&self.date, "%Y-%m-%d").unwrap()
    }
}
