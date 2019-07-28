$(document).ready(function() {

    // 配列内の最大値を取得する関数
    Array.max = function(array) {
        return Math.max.apply(Math, array);
    };

    // すべての値を取得
    var counts = $('#heat-map-3 tbody td').not('.stats-title').map(function() {
        return parseInt($(this).text());
    }).get();

    // 最大値を返す
    var max = Array.max(counts);

    // 色を指定する
    xr = 255;
    xg = 255;
    xb = 255;

    yr = 255;
    yg = 255;
    yb = 0;

    n = 100;


    // 各データポイントをループして、その％の値を計算する
    $('#heat-map-3 tbody td').not('.stats-title').each(function() {
        var val = parseInt($(this).text());
        var pos = parseInt((Math.round((val / max) * 100)).toFixed(0));

        red = parseInt((xr + ((pos * (yr - xr)) / (n - 1))).toFixed(0));
        green = parseInt((xg + ((pos * (yg - xg)) / (n - 1))).toFixed(0));
        blue = parseInt((xb + ((pos * (yb - xb)) / (n - 1))).toFixed(0));
        clr = 'rgb(' + red + ',' + green + ',' + blue + ')';
        $(this).css({
            backgroundColor: clr
        });

    });

});