#!/usr/bin/env python3

import logging
import argparse
import os
from urllib.parse import urlparse, unquote


import requests
import yaml
import html2text
from bs4 import BeautifulSoup

"""A Python script that makes migrating from WordPress to Flask as painless as
possible"""

__version__ = "1.0.1"

h2t = html2text.HTML2Text()
h2t.unicode_snob = True
# This option says it protects links from wrapping, but it doesn't
# https://github.com/Alir3z4/html2text/issues/425
# h2t.protect_links = True
# This option makes all lines reference links - very hard to keep track of
# h2t.wrap_links = False
# So, the inly viable option is to turn off the body_width limit
h2t.body_width = 0


def download_file(url: str, output_dir: str):
    response = requests.get(url)
    response.raise_for_status()
    filename = unquote(os.path.basename(urlparse(url).path))
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "wb") as output_file:
        output_file.write(response.content)


def get_wp_item_metadata(item) -> dict:
    item_metadata = dict()
    for meta in item.find_all("postmeta"):
        key = str(meta.find("meta_key").string)
        value = str(meta.find("meta_value").string)
        item_metadata[key] = value

    return item_metadata


def create_directory(path):
    if not (os.path.exists(path)):
        os.mkdir(path)
    elif not (os.path.isdir):
        raise ValueError(f"{path} already exists but is not a directory")


arg_parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    prog="wp2jekyll.py",
    description=__doc__)

arg_parser.add_argument("--version", action="version", version=__version__)
arg_parser.add_argument("xml_path",
                        help="the path to the WordPress export XML file")
arg_parser.add_argument("--output", default=".",
                        help="the directory to output to")
arg_parser.add_argument("--include-author", action="store_true",
                        help="include the author in the Front Data")
arg_parser.add_argument("--no-downloads", action="store_true",
                        help="do not attempt to download media files")
arg_parser.add_argument("--no-url-rewrites", action="store_true",
                        help="do not rewrite media URLs")
arg_parser.add_argument("--no-permalinks", action="store_true",
                        help="do not retain the original permalinks")
args = arg_parser.parse_args()
output_dir = args.output
with open(args.xml_path) as xml_file:
    raw_xml = xml_file.read()
create_directory(output_dir)
data_dir = os.path.join(output_dir, "_data")
create_directory(data_dir)
assets_dir = os.path.join(output_dir, "assets")
create_directory(assets_dir)
wp_contents_dir = os.path.join(assets_dir, "wp_contents")
create_directory(wp_contents_dir)
uploads_dir = os.path.join(wp_contents_dir, "uploads")
create_directory(uploads_dir)
posts_dir = os.path.join(output_dir, "_posts")
create_directory(posts_dir)
pages = os.path.join(output_dir, "_pages")
create_directory(pages)
wp_html_dir = os.path.join(output_dir, "_wp_html")
create_directory(wp_html_dir)
wp_html_posts_dir = os.path.join(wp_html_dir, "posts")
create_directory(wp_html_posts_dir)
wp_html_pages_dir = os.path.join(wp_html_dir, "pages")
create_directory(wp_html_pages_dir)

xml_soup = BeautifulSoup(raw_xml, features="xml")
wp_base_url = str(xml_soup.channel.base_site_url.string).rstrip("")
wp_uploads_url = f"{wp_base_url}/wp-content/uploads"
new_uploads_uri = "/assets/wp-content/uploads"
authors = xml_soup.channel.find_all("author")
with open(os.path.join(data_dir, "authors.yml"), "w",
          newline="\n") as authors_file:
    authors_ = {}
    for author in authors:
        authors_[str(author.author_login.string)] = dict(name=str(
            author.author_display_name.string))
    authors_file.write(yaml.dump(dict(authors_)))

rss_channel = xml_soup.rss.channel
posts = [x.parent for x in rss_channel.find_all("post_type", string="post")]
pages = [x.parent for x in rss_channel.find_all("post_type", string="page")]
attachments = [x.parent for x in rss_channel.find_all("post_type",
                                                      string="attachment")]

for attachment in attachments:
    attachment_url = str(attachment.attachment_url.string)
    download_dir = attachment_url.replace(wp_uploads_url, new_uploads_uri)
    download_dir = os.path.join(output_dir, download_dir)
    if not (args.no_downloads):
        try:
            download_file(attachment_url, download_dir)
        except requests.HTTPError as e:
            logging.warning(f"Could not download {attachment_url}: {e}")

items = posts + pages
for item in items:
    item_type = str(item.post_type.string)
    timestamp = f"{str(item.post_date_gmt.string)} -0000"
    if (timestamp == "0000-00-00 00:00:00 -0000"):
        # The post is a draft in WordPress
        timestamp = f"{str(item.post_modified_gmt.string)} -0000"
    last_modified_at = f"{str(item.post_modified_gmt.string)} -0000"
    local_date = str(item.post_date.string).split(" ")[0]
    name = str(item.post_name.string)
    title = str(item.title.string)
    author = str(item.creator.string)
    base_filename = f"{local_date}-{name}"
    publish = str(item.status.string) == "publish"
    pin = str(item.status.is_sticky) == "1"
    description = item.find("description")
    if description is not None:
        description = str(description.string)
        if (description == ""):
            description = None
    excerpt = item.find("excerpt")
    if excerpt is not None:
        excerpt = str(excerpt.string)
        if (excerpt == ""):
            excerpt = None
    if description is None:
        description = excerpt
    permalink = str(item.link.string).replace(wp_base_url, "")
    content = str(item.encoded.string)
    content_markdown = h2t.handle(content)
    categories = [str(x.string) for x in item.find_all(domain="category")]
    tags = [str(x.string) for x in item.find_all(domain="post_tag")]
    image = None
    item_metadata = get_wp_item_metadata(item)

    if "_thumbnail_id" in item_metadata:
        image = dict()
        thumbnail_id = item_metadata["_thumbnail_id"]
        thumbnail_item = rss_channel.find_all("post_id",
                                              string=thumbnail_id)[0].parent
        thumbnail_metadata = get_wp_item_metadata(thumbnail_item)
        image["path"] = str(thumbnail_item.attachment_url.string)
        if "_wp_attachment_image_alt" in thumbnail_metadata:
            image["alt"] = thumbnail_metadata["_wp_attachment_image_alt"]
    seo_title = None
    if "_yoast_wpseo_title" in item_metadata:
        seo_title = item_metadata["_yoast_wpseo_title"]
    if "_yoast_wpseo_metadesc" in item_metadata:
        description = item_metadata["_yoast_wpseo_metadesc"]
    front_data = dict(
        layout=item_type,
        permalink=permalink,
        title=title,
        seo_title=seo_title,
        description=description,
        date=timestamp,
        last_modified_at=last_modified_at,
        author=author,
        publish=publish,
        pin=pin,
        image=image,
        categories=categories,
        tags=tags
    )
    for key in ["description", "image", "seo_title"]:
        if front_data[key] is None:
            front_data.pop(key)
    if not (args.include_author):
        front_data.pop("author")
    if (args.no_permalinks):
        front_data.pop("permalink")
    if not (args.no_url_rewrites):
        permalink.replace(wp_base_url, "")

    front_data = yaml.dump(front_data,
                           default_flow_style=False,
                           sort_keys=False)

    html_path = os.path.join(wp_html_dir, f"{item_type}s",
                             f"{base_filename}.html")
    with open(html_path, "w", newline="\n") as html_file:
        html_file.write(content)
    md_file_content = f"---\n{front_data}---\n{content_markdown}"
    if not (args.no_url_rewrites):
        md_file_content = md_file_content.replace(wp_uploads_url,
                                                  new_uploads_uri)
    markdown_path = os.path.join(output_dir, f"_{item_type}s",
                                 f"{base_filename}.md")
    with open(markdown_path, "w", newline="\n") as md_file:
        md_file.write(md_file_content)
