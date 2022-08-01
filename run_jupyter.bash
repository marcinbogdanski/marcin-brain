docker run -d --rm -v /home/marcin/marcin-notes:/home/appuser/app/marcin-notes -v /home/marcin/.ssh/id_rsa:/home/appuser/id_rsa:ro -p 9999:9999 -e JUPYTER_PORT=9999 -e JUPYTER_PASSWORD=sha1:2b88e8fc1b92:14583de5a78e330b0637266a77cb76dc95cfc6f4 marcin-brain

