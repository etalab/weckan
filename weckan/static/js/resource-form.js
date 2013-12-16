/**
 * Forms specific features
 */
(function($, Utils, Config){

    "use strict";

    var SELECTOR = 'input[name="resource_type"]';

    function handle_resource_type() {
        var $checked = $(SELECTOR + ':checked');

        if (!$checked.length) {
            return;
        }

        if ($checked.val() == 'file.upload') {
            $('#url-id').attr('required', null).closest('.form-group').hide();
            $('#file-id').attr('required', 'required').closest('.form-group').show();
        } else {
            $('#url-id').attr('required', 'required').closest('.form-group').show();
            $('#file-id').attr('required', null).closest('.form-group').hide();
        }
    }

    $(function() {
        // Handle conditionnaly optional file upload or url
        $('input[name="resource_type"]').change(handle_resource_type);
        handle_resource_type();
    });

}(window.jQuery, window.Utils, window.EtalabConfig));
