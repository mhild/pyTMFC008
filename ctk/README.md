# TM Forum Conformance Test Kit (CTK)

`run-api-ctk.sh` runs the official **TMF638 v5.0.0 API CTK** (Docker image `tmforumorg/tmf638-v5.0.0-ctk:1.0.1`, Cypress)
against this project's API. The kit is not part of the repository: the script downloads the zip from TM Forum into
`ctk/work/` (git-ignored; the zip carries no license file), verifies its SHA-256 and uses it from there.

```bash
docker compose --profile postgres up -d --build     # or any other way to run the app, see the main README
ctk/run-api-ctk.sh                                  # the `app` service of this compose project
ctk/run-api-ctk.sh http://some-host:8080            # any other API the CTK container can reach
```

The script

* picks the image platform from `uname -m` (`linux/amd64` or `linux/arm64`; the image is ~680 MB, pulled on the first run),
* connects the `app` container to the Docker network `tmf` of the kit under the alias `tmf638-ri` and sets
  `config.json`'s `url` to `http://tmf638-ri:8000` (the kit appends `/service`, so no `/tmf-api/...` prefix is needed),
* runs the kit's `run.sh` and leaves the result in `ctk/work/ctk/REPORT.HTML` (open it in a browser; all mandatory test
  cases must pass).

Prerequisites: Docker, `curl`, `python3`. The API has to run with a database; the data of the run stays in it.

## Notes

* The kit calls `DELETE /tmf-ri-admin/v1/clear-all-data` before a run and ignores the `404` (not implemented here), and
  expects `404` for URLs containing `ctk-missing-id`.
* The payloads it creates and patches are in the kit's `config.json` (`payloads.Service.POST` / `PATCH`); they pass this
  API's schema validation unchanged.
* Last run: 37 tests, 37 passing (PostgreSQL, history off).
* The **component CTK** for TMFC008 (`TMFC008-ServiceInventory/CTK/componentCTK` in
  [tmforum-rand/TMForum-ODA-Ready-for-publication](https://github.com/tmforum-rand/TMForum-ODA-Ready-for-publication))
  tests the component as part of an ODA Canvas (Kubernetes + Helm) and is not covered here.
