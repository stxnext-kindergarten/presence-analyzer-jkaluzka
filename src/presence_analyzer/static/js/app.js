function parseInterval(value) {
    var result = new Date(1, 1, 1);
    result.setMilliseconds(value * 1000);
    return result;
}

var link = "/mean_time_weekday";

google.load("visualization", "1", {
    packages: ["corechart", "timeline"],
    'language': 'en'
});

(function ($) {
    $(document).ready(function () {
        var loading = $('#loading');
        $.getJSON("/api/v1/users", function (result) {
            var dropdown = $("#user_id");
            $.each(result, function (item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name));
            });
            dropdown.show();
            loading.hide();
            $('#header').find('#selected').removeAttr('id');
            $('a[href="' + link + '"]').parents('li').attr('id', 'selected');
        });

        $('#user_id').change(function () {
            var selected_user = $("#user_id").val();
            $.getJSON('/api/v1/user/' + selected_user + '/photo', function (result) {
                $.each(result, function (item) {
                    $('#user_photo').html('<img src=' + this.user_photo + '>');
                });
            });
            var chart_div = $('#chart_div');
            if (selected_user) {
                loading.show();
                chart_div.hide();
                load_data(selected_user, chart_div, loading);
            }
        });
    });
})(jQuery);
