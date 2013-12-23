/**
 * Membership requests specific features
 */
(function($, Utils, Config, swig) {

    "use strict";

    var msg_container = 'section.form .container',
        row_tpl = swig.compile($('#extra-row-template').text()),
        editableKeyOpts = {
            send: 'always',
            url: window.location,
            params: function(params) {
                var value = $(this).closest('tr.extra').find('a.value').text();
                return {
                    key: params.value,
                    old_key: params.pk,
                    value: $.trim(value),
                }
            },
            success: function(response, value) {
                $(this).data('pk', value);
                $(this).closest('tr.extra').find('a.value').data('pk', value);
            }
        },
        editableValueOpts = {
            send: 'always',
            url: window.location,
            params: function(params) {
                return {
                    key: params.pk,
                    value: params.value
                }
            }
        };

    function extra_remove_handler() {
        var $this = $(this),
            $row = $this.closest('tr'),
            key = $.trim($row.find('a.key').text()),
            $modal = $('#confirm-delete-modal');

        Utils.ensure_user(Utils.i18n('login-for-extras'));

        $modal.modal();
        $modal.find('.modal-footer .btn-primary').off('click').click(function() {
            $.ajax({
                url: window.location + '/' + key,
                type: 'DELETE',
                success:  function(data) {
                    var msg = Utils.i18n('extra-deleted');
                    Utils.success(msg, msg_container);
                    $row.remove();
                }
            }).error(function(e) {
                var msg = Utils.i18n('extra-error');
                Utils.error(msg, msg_container);
                console.error(e.responseJSON);
            }).always(function() {
                $modal.modal('hide');
            });
            return false;
        });

        return false;
    }


    $(function() {

        $('tr.extra a.key').editable(editableKeyOpts);
        $('tr.extra a.value').editable(editableValueOpts);

        $('a.extra-add').click(function() {
            var $row = $(this).closest('tr'),
                data = {
                    key: $.trim($row.find('#new-key').val()),
                    value: $.trim($row.find('#new-value').val())
                };

            Utils.ensure_user(Utils.i18n('login-for-extras'));
            $.post(window.location, data, function(data) {
                var $row = $(row_tpl(data));
                $row.appendTo('.extras-table tbody');
                $row.find('a.key').editable(editableKeyOpts);
                $row.find('a.value').editable(editableValueOpts);
                $row.find('a.extra-remove').click(extra_remove_handler);
            }).error(function(e) {
                var msg = Utils.i18n('extra-error');
                Utils.error(msg, msg_container);
                console.error(e.responseJSON);
            }).always(function() {
                $row.find('input').val('');
            });
            return false;
        });

        $('a.extra-remove').click(extra_remove_handler);
    });

}(window.jQuery, window.Utils, window.EtalabConfig, window.swig));
