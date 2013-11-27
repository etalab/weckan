/**
 * Forms specific features
 */
(function($, Utils, VALIDATION_RULES){

    "use strict";

    $(function() {
        // jQuery validate
        $('form.validation').validate(VALIDATION_RULES);

        // Bootstrap select
        $('.selectpicker').selectpicker();

        // Markdown editor
        $('textarea.md').markdown({
            autofocus: false,
            savable: false
        });

        // Publisher card handling
        $('.publisher-card, .publisher-card a').click(function() {
            var $card = $(this).closest('.publisher-card'),
                $input = $card.closest('.form-group').find('input[type="hidden"]'),
                org_id = $card.data('org-id');

            $(this).closest('.card-list').find('.publisher-card').removeClass('active');
            $card.addClass('active');

            $input.val(org_id);

            return false;
        });
    });

}(window.jQuery, window.Utils, window.ETALAB_VALIDATION_RULES));
