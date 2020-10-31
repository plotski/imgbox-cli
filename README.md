CLI tool for uploading images to [https://imgbox.com/](imgbox.com).

### Usage

```sh
$ imgbox foo.jpg bar.png --title "My Gallery" --thumb-width 500
$ imgbox --thumb-width 123 < list_of_file_paths.txt
$ generate_file_paths | imgbox --json | jq -r ".[].image_url"
```

### BBcode

```sh
while read image; do
    success=$(jq -r '.success' <<< "$image")
    if [ "$success" != 'true' ]; then
        error="$(jq -r '.error' <<< "$image")"
        filename="$(jq -r '.filename' <<< "$image")"
        echo "$filename: $error" >&2
    else
        image_url=$(jq -r '.image_url' <<< "$image")
        thumbnail_url=$(jq -r '.thumbnail_url' <<< "$image")
        echo "[url=$image_url][img]$thumbnail_url[/img][/url]"
    fi
done <<< $(imgbox --json "$@" | jq -c '.[]')
```

### Installation

```sh
$ sudo apt install pipx
$ pipx install --upgrade imgbox-cli
```
