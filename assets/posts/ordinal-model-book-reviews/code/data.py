import polars as pl

ratings = pl.read_csv("goodreads-10k-ratings.csv")
summaries = pl.read_csv("goodreads-10k-books.csv")
books = summaries.join(ratings, on="book_id", how="left").with_row_index()

top_books = books["book_id", "ratings_count"].unique().sort("ratings_count")[-100:]

TRAIN_PERCENT = 0.2

train = (
    books.filter(pl.col("book_id").is_in(top_books["book_id"].to_list()))
    .with_columns(
        row_num=pl.int_range(pl.len()).over("book_id"),
        total_rows=pl.len().over("book_id"),
    )
    .filter(pl.col("row_num") < (TRAIN_PERCENT * pl.col("total_rows")).ceil())
)

test = (
    books.filter(
        pl.col("book_id").is_in(top_books["book_id"].to_list()),
        ~pl.col("index").is_in(train["index"].to_list()),
    )
    .group_by(
        "book_id",
    )
    .head(100)
)

book_id_map = {k: i + 1 for i, k in enumerate(train["book_id"].unique())}
user_id_map = {k: i + 1 for i, k in enumerate(train["user_id"].unique())}

train = train.with_columns(
    index=pl.row_index(),
    clean_book_id=pl.col("book_id").replace_strict(book_id_map),
    clean_user_id=pl.col("user_id").replace_strict(user_id_map),
).drop("isbn")

test = test.with_columns(
    index=pl.row_index(),
    clean_book_id=pl.col("book_id").replace_strict(book_id_map, default=0),
    clean_user_id=pl.col("user_id").replace_strict(user_id_map, default=0),
).drop("isbn")

train.write_csv("train.csv")
test.write_csv("test.csv")
