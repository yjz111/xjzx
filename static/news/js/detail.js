function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    comment_list_vue = new Vue({
        el: '.comment_list_con',
        delimiters: ['[[', ']]'],
        data: {
            comment_list: []
        }
    });
    // 收藏
    $(".collection").click(function () {
        $.post('/collect',{
            'news_id':$('#news_id').val(),
            'csrf_token':$('#csrf_token').val()
        },function (data) {
            if(data.result==1){
                alert('请指定收藏的新闻');
            }else if(data.result==2){
                alert('请先登录');
            }else if(data.result==3){
                alert('指定的新闻编号无效');
            }else if(data.result==4){
                // alert('收藏成功');
                $('.collection').hide();
                $('.collected').show();
            }else if(data.result==5){
                alert('此新闻已经被收藏');
            }
        });
    })

    // 取消收藏
    $(".collected").click(function () {
        $.post('/collect',{
            'news_id':$('#news_id').val(),
            'csrf_token':$('#csrf_token').val(),
            'flag':'2'//操作标记，2表示取消收藏
        },function (data) {
            if(data.result==1){
                alert('请指定取消收藏的新闻');
            }else if(data.result==2){
                alert('请先登录');
            }else if(data.result==3){
                alert('指定的新闻编号无效');
            }else if(data.result==4){
                // alert('取消收藏成功');
                $('.collection').show();
                $('.collected').hide();
            }else if(data.result==5){
                alert('此新闻未被收藏，无法取消');
            }
        });
    })

    // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();
        $.post('/comment_add', {
            'msg': $('.comment_input').val(),
            'news_id': $('#news_id').val(),
            'csrf_token': $('#csrf_token').val()
        }, function (data) {
            if (data.result == 1) {
                alert('请先登录');
            } else if (data.result == 2) {
                alert('请填写评论信息');
            } else if (data.result == 3) {
                alert('新闻编号非法');
            } else if (data.result == 4) {
                $('.comment_input').val('');
                load_comment_list();
            } else if (data.result == 5) {
                alert('数据保存失败');
            }
        });
    })

    $('.comment_list_con').delegate('a,input', 'click', function () {

        var sHandler = $(this).prop('class');
        //回复
        if (sHandler.indexOf('comment_reply') >= 0) {
            $(this).next().toggle();
        }
        //取消回复
        if (sHandler.indexOf('reply_cancel') >= 0) {
            $(this).parent().toggle();
        }
        //点赞
        if (sHandler.indexOf('comment_up') >= 0) {
        var $this = $(this);
        var up = 0;
        if (sHandler.indexOf('has_comment_up') >= 0) {
            // 如果当前该评论已经是点赞状态，再次点击会进行到此代码块内，代表要取消点赞
            $this.removeClass('has_comment_up');
            up = 0;
        } else {
            $this.addClass('has_comment_up');
            up = 1;
        }

    $.post('/comment_up', {
        'csrf_token': $('#csrf_token').val(),
        'comment_id': $this.parents('.comment_list').attr('id'),
        'up': up
    }, function (data) {
        if (data.result == 1) {
            $this.text(data.count);
        }
    });
}
        //提交回复
        if (sHandler.indexOf('reply_sub') >= 0) {
            //获取回复内容
            var msg=$(this).prev().val();
            //清空内容
            $(this).prev().val('');
            //隐藏回复
            $(this).parent().toggle();
            $.post('/comment_add', {
                'msg': msg,
                'comment_id': $(this).attr('name'),
                'news_id': $('#news_id').val(),
                'csrf_token': $('#csrf_token').val()
            }, function (data) {
                if (data.result == 1) {
                    alert('请先登录');
                } else if (data.result == 2) {
                    alert('请填写评论信息');
                } else if (data.result == 3) {
                    alert('新闻编号非法');
                } else if (data.result == 4) {
                    load_comment_list();
                } else if (data.result == 5) {
                    alert('数据保存失败');
                }
            });
        }
    })

    // 关注当前新闻作者
    $(".focus").click(function () {

    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {

    })


    load_comment_list();
})

function load_comment_list() {
    $.get('/comment_list/' + $('#news_id').val(), function (data) {
        comment_list_vue.comment_list = data.clist;
        $('.comment_count span').text(data.count);
    });
}