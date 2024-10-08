# wp2jekyll

A Python script that makes migrating from WordPress to [Jekyll][0] as painless as
possible.

I wrote this script after going through the [painful process][1] of manually
migrating my WordPress blog to Jekyll because no existing migration tools
met my needs.

## Features

This CLI script takes a WordPress export XML file and:

- Downloads all media content from the WordPress blog
- Converts pages and posts from HTML to Markdown with `html2text`
- Replaces media URLs in the Markdown content to the new relative URIs
- Includes useful information in the Jekyll [Front Data][2] YAML

## How is this different than the Jekyll Exporter Wordpress plugin?

wp2jekyll does a few things that Jeyll Eporter [WordPress plugin][8]
by Ben Balter does not:

- By default, wp2jekyll will retain the existing permalink of posts and pages, so incoming links don't break.
- Rather than just dumping all WordPress post metadata to YAML in the Front Data, wp2jekyll only retains items useful for SEO (i.e, the featured image and Yoast metadata), and maps them to variable names that are expected by many Jekyll themes. This makes the Front Data much cleaner and useful.
- By default, wp2jekyll adjusts image/attachment URLs to be relative to the assets directory.
- wp2jekyll keeps a copy of the original post HTML outside of the Jekyll build path so you can look at that in case the Markdown conversion botched some content.

## Front Data

How the Front Data is used depends on the Jekyll theme in use. The Front Data
generated by `wp2jekyll` is designed for use with the [Chirpy][3] theme, but
many other themes use the same variable names, so it should work as-is for
other themes too.

**Variable**                                         | **Description**
-----------------------------------------------------|----------------------------------------------------------
`layout` | The layout to use (i.e., `post`, or `page`)
`permalink` | Sets the URI of the post or page so it matches the WordPress one
`title` | The post title
`seo_title` | The SEO title from Yoast SEO - not currently used by any Jekyll theme
`description` | The description from the WordPress or Yoast SEO description fields
`date` | The GMT timestamp of the post or page in `YYYY:MM:DD HH:MM SS -0000` format
`last_modified_at` | The GMT modification timestamp of the post or page in `YYYY:MM:DD HH:MM SS -0000` format
`image:`<br><code>  path</code>:<br><code>  alt</code>:| Path to the featured image and optional `alt` text
`publish` | Sets if the post or page is published (`True` or `False`)
`pin` | Sets if the post or page is pinned (`True` or `False`)
`categories` | A list of categories
`tags` | A list of tags

## Output

- `_data/authors.yaml` - A mapping of WordPress login names to display names
- `_assets/wp-content/uploads` - Files uploaded to WordPress
- `_posts/` - Posts converted to Markdown format
- `_pages/` - Pages converted to Markdown format
- `_wp_html/pages` - WordPress content in the original HTML
- `_wp_html/posts` - WordPress content in the original HTML

## Requirements

Python >= 3.2

Install the Python dependencies before using `wp2jekyll`.

```bash
python3 -m pip install -r requirements.txt
```

## Use

Navigate to Tools> Export in the WordPress admin console to export the WordPress
blog content to XML.

Pass the path to this file to `wp2jekyll`, along with any desired options.

For example:

```bash
python3 wp2jekyll.py seanthegeeknet.WordPress.2024-08-12.xml
```

## Known issues when converting to Markdown

`wp2jekyll` uses `html2text` to convert the WordPress HTML content to Markdown.
It's not perfect. Here are some issues I ran into.

### No nested tables

Markdown does not support nested tables, but Markdown does support HTML
inside of a Markdown document. If you have a document with a nested table,
replace the entire (i.e., outer) table with the HTML in the original post
or page.

### iframe tags are removed

In HTML, `iframe` tags are used to embed content from other websites, such as
YouTube. You will unfortunately need to copy and paste `iframe` content from
the original HTML into the Markdown document.

### No oEmbed support

WordPress supports [oEmbed][7], which allows a post author to embed social
media content just by placing the URL in the post body. oEmbed takes care of
generating the HTML to actually embed that content. Unfortunately, Jekyll does
not support oEmbed, and plugins that add oEmbed support have not been
maintained to be compatible with modern Jekyll.

So, look for social media URLs that are on their own, and replace them with the
proper HTML. The social media networks will provide the embed HTML as a
sharing option.

## CLI help

```text
usage: wp2jekyll.py [-h] [--version] [--output OUTPUT] [--include-author] [--no-downloads] [--no-url-rewrites] [--no-permalinks] xml_path

positional arguments:
  xml_path           the path to the WordPress export XML file

options:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  --output OUTPUT    the directory to output to (default: .)
  --include-author   include the author in the Front Data (default: False)
  --no-downloads     do not attempt to download media files (default: False)
  --no-url-rewrites  do not rewrite media URLs (default: False)
  --no-permalinks    do not retain the original permalinks (default: False)
  --no-cleanup       do not clean up the converted Markdown content (default: False)
```

[0]: https://jekyllrb.com/
[1]: https://seanthegeek.net/posts/my-painful-but-worthwhile-migration-from-wordpress-to-jekyll/
[2]: https://jekyllrb.com/docs/front-matter/
[3]: https://chirpy.cotes.page/posts/write-a-new-post/
[7]: https://oembed.com/
[8]: https://wordpress.org/plugins/jekyll-exporter/
