function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}



$(".focus").click(function () {
    var curr_this=$(this);
    $.post('/follow', {
        'csrf_token': $('#csrf_token').val(),
        'follow_user_id': $('#user_id').val(),
        'action': '1'
    }, function (data) {
        if (data.result == 1) {
            curr_this.hide();
            curr_this.next().show();
            var follows=parseInt($('.follows>b').text());
            follows++;
            $('.follows>b').text(follows);
        } else {
            $('.login_btn').click();
        }
    });
})

// 取消关注当前新闻作者
$(".focused").click(function () {
    var curr_this=$(this);
    $.post('follow', {
        'csrf_token': $('#csrf_token').val(),
        'follow_user_id': $('#user_id').val(),
        'action': '2'
    }, function (data) {
        if (data.result == 1) {
            curr_this.hide();
            curr_this.prev().show();
            var follows=parseInt($('.follows>b').text());
            follows--;
            if (follows <= 0) {
                follows = 0;
            }
            $('.follows>b').text(follows);
        } else {
            $('.login_btn').click();
        }
    });
})