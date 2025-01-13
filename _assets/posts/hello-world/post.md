I've tried starting a blog a number of times,
some of which I hosted and published some
content, others which never got to that
stage. 

While I don't set formal New Year resolutions,
I do use the turn of the year as motivation to try
new experiences, form new habits, and evaluate
life goals. I suppose that's what a New Year Resolution
actually is. Last year it was reading
50 books (I read 48). This year, I'm going 
to try to maintain this blog, which might be the
most daunting one yet. 

This site is written primarily
in [Rust](https://www.rust-lang.org),
using the [actix-web](https://actix.rs)
framework. [tera](
https://keats.github.io/tera/)
is used a HTML templating engine.
Posts are written
in Markdown, parsed using
[pulldown-cmark](
https://github.com/pulldown-cmark/pulldown-cmark
), and post metadata are pulled
in via [TOML](https://toml.io/en/)
files. I initially styled the site 
using [tailwindcss](
https://tailwindcss.com),
but reverted to raw CSS after finding
`tailwindcss` tags had become too messy
and hard to decipher.

I followed this great
blog by [Morton Vistisen](
https://mortenvistisen.com/posts/how-to-build-a-simple-blog-using-rust)
for piecing the backend and
frontend together.  

```rust

fn main() {
    let name = "conor";
    println!("Hello {}", name)
}
```

\\[ X \sim \mathrm{Normal}(0, 1) \\]

The design is minimal, and I have tried to
follow good design principles throughout:
pages should be clear and easy to read
on all devices, the navigation bar won't
fool you, the back button works as intended,
links are clearly hightlighted
and underlined. The styling -- light or dark --
is set depending on your browser's defaults.
If you notice any issues,
please reach out on the Github repository.
