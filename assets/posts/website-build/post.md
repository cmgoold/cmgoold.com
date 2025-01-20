In 2025, building your own website can be as easy
or hard as you want it to be.
There are plenty of platforms out there, of
varying prices, morals and ethics, that
can make you a website in minutes.
For people who want slightly more control,
there are a variety of static site generators
in the programming language of your choice, 
as well as easy hosting options such as 
Github pages. Or you could go with a dedicated
blogging platform such as [Bear Blog](
https://bearblog.dev/
), that provides a relatively cheap all-in-one service
with some degree of autonomy.

My approach to building this website was
not only to produce a site that I could
maintain completely independently,
following the IndieWeb [key principles](
https://indieweb.org/principles
), but also to 
learn more web development.
In particular, becoming more confident 
hooking up all the interlocking pieces 
of software needed
to host a website end-to-end. Here's how
I did it.

# Structure

If you're new to building software, even if
you have some coding experience, it can be
overwhelming learning which software does
what and interlacing all their dependencies
in the most optimal and safest manner. 
Personally, I find this the more difficult task
when approaching new software than using the
software itself.
So at a high level, this is what is going on to 
produce this web page:

* A backend web-framework written in [Rust](
https://www.rust-lang.org/), which builds
the HTML files from templates, handles all
the URL routing, CSS styling, and serves the site on the
local web server of the machine running the code.

* The Rust code is packaged into a [Docker](
https://www.docker.com) container,
meaning all the code can be served using a simple
call to `docker compose up`.

* The code is hosted at a [Github repository](
https://github.com/cmgoold/cmgoold.com/),
and Github Action [workflows](
https://github.com/cmgoold/cmgoold.com/blob/main/.github/workflows/deploy.yaml) are used to build
the Docker image and copy it to a [Hetzner](
https://www.hetzner.com/
)
virtual private
server connected to the internet and remotely
accessible with SSH.
The builds are currently only triggered on
merged pull requests to the `main`
branch, but another possibility
is to set up automated builds at a cadence
that makes sense.


* The virtual server's IP address points to
my domain name `cmgoold.com`, meaning I can use
`http://cmgoold.com:<port>` to access my website
rather than `http://<long-ip-address>:<port>`.

* Finally, I use [nginx](https://nginx.org/en/)
 as a reverse proxy to route
`http://cmgoold.com:<port>` to both `http://cmgoold.com`
and it's safer default variant `https://cmgoold.com`.
Of course, you can just type `cmgoold.com` and it will
take you to the HTTPS-enabled site directly, all thanks
to nginx.

## Building a website using Rust

This website's tooling
is no doubt overkill for what could
have been made via any of the static site generators
out there. But I've been dappling with Rust for
a little while now, and wanted a more involved
project to build some Rust muscle memory.
I would also like to maintain this site in the long
term and its functionality is still open-ended.
The current setup provides me autonomy
and flexibility.

I am using the Rust crate [`actix_web`](
https://docs.rs/actix-web/latest/actix_web/
) as the web framework. Rust has a number of
crates for web development, although none
quite as expansive as something like [Ruby on Rails](
https://rubyonrails.org)
or Python's [Django](https://www.djangoproject.com) 
or PHP's [Laravel](https://laravel.com).
`actix_web` appeared to be relatively mature
compared to some other Rust crates, and has features
such as asynchronous handlers.

Here's the 'hello world' equivalent for
web development in `actix_web`. Assuming
you have Rust installed, run:

```bash
cargo new my-site && cd my-site
```

and edit the `Cargo.toml` file to include:

```toml
[dependencies]
actix-web = "4" # change to the most recent version
```

In `src/main.rs`, add the following code:

```rust
use actix_web::{get, web, App, HttpServer, Responder};

#[get("/")]
async fn index() -> impl Responder {
    "Hello, World!"
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| App::new().service(index))
        .bind(("127.0.0.1", 8080))?
        .run()
        .await
}
```

Enter `http://127.0.0.1:8080` into your web browser
and you should see "Hello, World!" on a blank page.

The code for this small example is available in this
post's directory at the [Github repository](
https://github.com/cmgoold/cmgoold.com/blob/main/assets/posts/website-build/my-site/).

I initially followed the blog by [Morten Vistisen](
https://mortenvistisen.com/posts/how-to-build-a-simple-blog-using-rust) to create this website, but the above bare-bones
approach is really all you need to get started.
You can expand by defining additional service functions
(like `index()` above) in a separate file, like the 
[`handlers.rs`](
https://github.com/cmgoold/cmgoold.com/blob/main/src/handlers.rs
) file I use, and adding in HTML templates using
[Tera](https://keats.github.io/tera/docs/), to which you
can layer on CSS styling or other frameworks of your choice.

## Writing posts in Markdown

I'm not the biggest lover of mark-up languages
like Markdown or reStructuredText.
I'm perhaps one of the minority that
like to retain the control of the lower-level
language and not add an additional package to the
workflow. I've also run into issues before with static site
generators where certain HTML classes are not clearly
accessible, and other odd bugs, which might entail
strange hacks to get working. 
However, for a simple blog like this, 
Markdown *should* be fine.

That aside, this site uses `pulldown_cmark` to turn
Markdown into HTML and inject it into the [`post.html`](
https://github.com/cmgoold/cmgoold.com/blob/main/assets/templates/post.html) template file.
The post metadata is stored in a `metadata.toml` TOML file.
This ideal was taken from [Morten Vistisen](
https://mortenvistisen.com/posts/how-to-build-a-simple-blog-using-rust)'s blog post.

One option I am considering is re-factoring the code
to write metadata and posts directly in HTML, and scrape
the metadata and post body using Rust to inject again
into the template file. It's a bit circuitous, going
from HTML to Rust to HTML, but would allow me to write
everything I need in a new post in a single HTML
file in a simpler file structure.

## Choosing Hetzner

I deliberated for a quite a while on how to actually
host this site. I wanted to go with a more local
company that used renewable energy to power their
own servers, like Krystal, but I also wanted control
over how I deployed my website. I wanted to spin up
a Docker image directly, and I couldn't quite see
how that was possible with some of my preferred
vendors. Hetzner is a well-known name in the area
with servers in Europe that are well-protected by
data protection laws. They have a pretty good
[sustainability statement](https://www.hetzner.com/unternehmen/nachhaltigkeit/)
that mentions renewable energy, although I found
it slightly more difficult to find than some
other options. Take from that what you will,
I'm definitely not an expert on this topic.

In terms of cost, I chose the cheapest plan
at about $5 per month, which is a shared vCPU
with 4 GB of RAM and 40 GB of inbuilt storage.
I think this will be fine for my needs,
and I wouldn't want to spend anything more than
$5 a month.
They have plenty of additional plans should
you need it, or I in the future, however.

The Hetzner setup was pretty smooth sailing if you're
comfortable with basic server terminology and
logging in remotely by, ideally, SSH.

# nginx reverse proxy

To clean up the site URLs, I used nginx
as a reverse proxy, along with using [Let's Encrypt](
https://letsencrypt.org/
)
and [Certbot](
https://certbot.eff.org/
) to generate SSL certificates to enable HTTPS.
I added nginx into my [`compose.prod.yaml`](
https://github.com/cmgoold/cmgoold.com/blob/main/compose.prod.yaml
) file.

You can see my [`nginx.conf`](
https://github.com/cmgoold/cmgoold.com/blob/main/nginx/nginx.conf
) file if you need the details, and how it
interacts with with the `compose.prod.yaml` workflow.
One simple tip if you are going this route: use 
`docker compose up` rather than `docker compose up -d`
to build your site when developing, as you can more
clearly see the logs. I couldn't get the reverse proxy
to work for quite a while due to not seeing an erroneous
path that was assumed in the `nginx.conf` file but
hadn't created in the Docker container. Running `docker compose
up -d` swallowed the warning/error message, and I was left
with just the nginx server running but no re-routing
of my host URIs.

## Adding tests

I still need to add unit and integration tests for this site.
I have a development Docker compose file that is built as a 
Github action, but that's only a placeholder for more
specific end-to-end tests.
