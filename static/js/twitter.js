var timeout;

$(document).ready(function(){
    timeout = window.setTimeout(updater.pool, updater.timer);
    $("#stop").click(function(){
        window.clearTimeout(timeout);
        updater.statusEnable = false;
        $("#start").toggle();
        $("#stop").toggle();     
    })

    $("#start").click(function(){
        timeout = window.setTimeout(updater.pool, updater.timer);
        updater.statusEnable = true;
        $("#start").toggle();
        $("#stop").toggle();
    })

    $(document).bind('keydown', 'ctrl+r', updater.pool);
    $(document).bind('keydown', 'ctrl+k', function(){
        $('.new').removeClass('new');
        document.title = "Twitter Example"
    });

    $("abbr.timeago").timeago()
 
})

var updater = {
    timer: 600000,
    refreshEnabled: true,
    isRefreshing: false,

    pool: function(){
        if(updater.isRefreshing){
            return;
        } else {
            updater.isRefreshing = true;
        }

        $(".status").text('refreshing').fadeIn(300);

        var args = { 'since': $(".post:first")[0].id };
        $.ajax({ url:'/', type: "POST", data: $.param(args), success: updater.success,
                 error: updater.error})
    },

    success: function(response){
        updater.isRefreshing = false;
        $(".status").fadeOut(300);
        var posts = JSON.parse(response);

        for(var p in posts){
            var post = posts[p];
            var html = $(post['html']);
            html.hide();
            html.addClass('new');
            $("#stream").prepend(html);
            html.slideDown(300);
        }

        $("abbr.timeago").timeago()

        if(posts.length != 0){
            document.title = $('.new').length + " - Twitter Example"
        }

        if(updater.statusEnable){
            updater.timer = 10000;
            timeout = window.setTimeout(updater.pool, updater.timer);
        }
        
    },

    error: function(response){
        $(".status").text('error!').fadeIn(300).delay(800).fadeOut(300);
        updater.isRefreshing = false;
        if(updater.statusEnabled){
            updater.timer *= 1.5;
            timeout = window.setTimeout(updater.pool, updater.timer);
        }
    }
}
