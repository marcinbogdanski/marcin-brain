Initial readme


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