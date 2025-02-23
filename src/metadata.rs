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
    pub fn string_date_to_datetime(&self, name: &'static str) -> NaiveDate {
        if name == "edited" && self.edited_date.is_some() {
            let edited = match &self.edited_date {
                Some(d) => d,
                None => ""
            };
            NaiveDate::parse_from_str(&edited, "%Y-%m-%d").unwrap()
        } else {
            NaiveDate::parse_from_str(&self.date, "%Y-%m-%d").unwrap()
        }
    }
}
