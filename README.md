# Marcin Brain

This repo performs two functions:
* Jupyter Notebook server for Marcin notes
* Anki sync script from Marcin notes

# Build And Run

## Build Container
```
docker build -t marcin-brain .
```

## Generate Password (optional)

* run docker container: `docker run -it --rm marcin-brain`
* run python interpreter: `python`
* execute python commands
  * `from notebook.auth import passwd`
  * `passwd(algorithm='sha1')`
  * then enter and verify password
  * you should see password hash in form:
    * `sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed`

## Run Container

__Option #1: Quick Run__

```
docker run -d -p 9999:9999 -e JUPYTER_PORT=9999 -e JUPYTER_PASSWORD=sha1:2b88e8fc1b92:14583de5a78e330b0637266a77cb76dc95cfc6f4 marcin-brain
```

__Option #2: Run With Env File__

Create `dotenv.env` file:

```bash
JUPYTER_PASSWORD=sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed
JUPYTER_PORT=9999
```

Launch container:

```
docker run -it --rm -p 9999:9999 --env-file dotenv.env marcin-brain
```

or with docker-compose

```
docker-compose --env-file dotenv.env up
```

## Git Checkout

Inside container

```
git config --global credential.helper store
git clone https://github.com/marcinbogdanski/marcin-notes.git
```

Provide Git username and Personal Access Token (PAT)

## Run with external storage and SSH Agent (advanced)

Run container

```bash
docker run -d --rm -v /home/marcin/marcin-notes:/home/appuser/app/marcin-notes -v /home/marcin/.ssh/id_rsa:/home/appuser/id_rsa:ro -p 9999:9999 -e JUPYTER_PORT=9999 -e JUPYTER_PASSWORD=sha1:2b88e8fc1b92:14583de5a78e330b0637266a77cb76dc95cfc6f4 marcin-brain
```

Then inside container:

```
eval "$(ssh-agent -s)"
ssh-add -L
ssh-add /home/appuser/id_rsa
```



# Run on EC2

__Start EC2 Instance__

See instructions in `marcin-notes/300_CS/Linux_Server.ipynb`

# Old Readme

**Install for User**

Add following to your .bashrc and restart terminal

```bash
export PYTHONPATH=${PYTHONPATH}:$HOME/marcin-brain
export PATH=$PATH:$HOME/marcin-brain/scripts
```

**Anki DB Requirements**

This repo requires you create new card type **Basic-MathJax** as explained [here](https://www.reddit.com/r/Anki/comments/a0x5qt/displaying_mathjax_in_ankidroid_while_staying/)

Paste this code at the end of your Front **and** Back Templates:

```html
<script type="text/x-mathjax-config">
    MathJax.Hub.processSectionDelay = 0;
    MathJax.Hub.Config({
        messageStyle:"none",
        showProcessingMessages:false,
        tex2jax:{
            inlineMath: [ ['$','$'], ['\\(','\\)'] ],
            displayMath: [ ['$$','$$'], ['\\[','\\]'] ],
            processEscapes:true
        }
});
</script>
<script type="text/javascript">
(function() {
  if (window.MathJax != null) {
    var card = document.querySelector('.card');
    MathJax.Hub.Queue(['Typeset', MathJax.Hub, card]);
    return;
  }
  var script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS_SVG-full';
  document.body.appendChild(script);
})();
</script>
```

