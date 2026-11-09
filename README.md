# SpeedyIndex index check — GitHub Action

Check after every deploy whether your pages are in Google's, Bing's or Yandex's index, using SpeedyIndex, a service for link indexing and index checking. The action reads your sitemap (or a URL list), creates a [SpeedyIndex API](https://en.speedyindex.com/api.php) task and writes the indexed / unindexed URLs to the job summary. It can also submit new URLs for indexing.

## Usage

```yaml
name: Index check
on:
  schedule:
    - cron: "0 6 * * 1"   # every Monday
  workflow_dispatch:

jobs:
  index-check:
    runs-on: ubuntu-latest
    steps:
      - uses: uskotoivo81-netizen/speedyindex-action@v1
        with:
          api-key: ${{ secrets.SPEEDYINDEX_API_KEY }}
          sitemap: https://example.com/sitemap.xml
          engine: google
          max-urls: 500
          wait-minutes: 20
```

Submit the newest URLs for indexing after a deploy (spends your SpeedyIndex balance):

```yaml
      - uses: uskotoivo81-netizen/speedyindex-action@v1
        with:
          api-key: ${{ secrets.SPEEDYINDEX_API_KEY }}
          sitemap: https://example.com/sitemap.xml
          mode: index
          max-urls: 50
```

## Inputs

| Input | Default | Description |
|---|---|---|
| `api-key` | — | SpeedyIndex API key, from a repository secret |
| `sitemap` | — | Sitemap or sitemap index URL |
| `urls-file` | — | File with one URL per line |
| `engine` | `google` | `google`, `bing` or `yandex` (Bing: checks only) |
| `mode` | `check` | `check` or `index` |
| `max-urls` | `1000` | Newest URLs first when the sitemap has `lastmod` |
| `wait-minutes` | `20` | How long to wait for the check report (`0` = don't wait) |
| `fail-on-unindexed` | `false` | Fail the job when unindexed URLs are found |

Outputs: `task-id`, `total`, `unindexed`.

## Notes

- Keep the API key in GitHub Secrets, never in the workflow file.
- A page with `noindex`, a 404 or a redirect will not be indexed: fix those first.
- The action uses the [`speedyindex`](https://pypi.org/project/speedyindex/) Python package.

## License

MIT
