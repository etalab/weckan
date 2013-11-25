/**
 * Homepage specific features
 */
(function($, Utils){

    "use strict";

    $(function() {
        // Update carousel ellipsis on change
        $('#home-carousel .title').on('slide.bs.carousel', function() {
            $(this).trigger('update');
        });

        // Async feature handling
        $('a.unfeature').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            if (!$this.hasClass('disabled')) {
                $.get(api_url, function(data) {
                    $this.removeClass('btn-warning').addClass('btn-danger').addClass('disabled');
                    $this.removeAttr('href').attr('title', Utils.i18n('is-unfeatured'));
                    Utils.success(Utils.i18n('is-unfeatured'));
                }).error(function(e) {
                    console.error(e);
                    Utils.error(Utils.i18n('featured-error'));
                });
            }

            return false;
        });
    });

}(window.jQuery, window.Utils));
