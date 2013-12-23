/**
 * Membership requests specific features
 */
(function($, Utils, Config, swig) {

    "use strict";

    var msg_container = 'section.form .container',
        group_title = $('section.form').data('group-title'),
        group_id = $('section.form').data('group-id'),
        mapping = {'{org}': group_title},
        row_tpl = swig.compile($('#member-row-template').text()),
        add_modal_tpl = swig.compile($('#member-add-template').text()),
        editableOpts = {
            url: window.location,
            source: [
                {value: 'admin', text: Utils.i18n('role-admin')},
                {value: 'editor', text: Utils.i18n('role-editor')},
                {value: 'member', text: Utils.i18n('role-member')},
            ]
        };

    function toggleEmpty() {
        if ($('tr.member').length > 0) {
            $('.empty').addClass('hide');
        } else {
            $('.empty').removeClass('hide');
        }
    }

    function member_remove_handler() {
        var $this = $(this),
            $row = $this.closest('tr'),
            username = $row.data('username'),
            $modal = $('#confirm-delete-modal');

        Utils.ensure_user(Utils.i18n('login-for-members'));

        $modal.modal();
        $modal.find('.modal-footer .btn-primary').off('click').click(function() {
            $.ajax({
                url: window.location + '/' + username,
                type: 'DELETE',
                success:  function(data) {
                    var msg = Utils.i18n('member-deleted', mapping);
                    Utils.success(msg, msg_container);
                    $row.remove();
                }
            }).error(function(e) {
                var msg = Utils.i18n('member-error', mapping);
                Utils.error(msg, msg_container);
                console.error(e.responseJSON);
            }).always(function() {
                toggleEmpty();
                $modal.modal('hide');
            });
            return false;
        });

        return false;
    }


    $(function() {

        $('.member-role').editable(editableOpts);

        $('.user-completer').on('typeahead:selected typeahead:autocompleted', function (e, data) {
            var $completer = $(this),
                $modal = $('#add-member-modal'),
                user = data;

            Utils.ensure_user(Utils.i18n('login-for-members'));

            $modal.find('.modal-body').html(add_modal_tpl(user));
            $modal.modal().off('hide.bs.modal').on('hide.bs.modal', function() {
                $completer.val('');
            });

            $modal.find('#add-button').off('click').click(function() {
                $.post(window.location, {pk: user.slug}, function(data) {
                    var $row = $(row_tpl(user));
                    $('tr.empty').before($row);
                    $row.find('.member-role').editable(editableOpts);
                    $row.find('.member-remove').click(member_remove_handler);
                }).error(function(e) {
                    var msg = Utils.i18n('member-error', mapping);
                    Utils.error(msg, msg_container);
                    console.error(e.responseJSON);
                }).always(function() {
                    toggleEmpty();
                    $modal.modal('hide');
                });
                return false;
            });

            return false;
        });

        $('a.member-remove').click(member_remove_handler);
    });

}(window.jQuery, window.Utils, window.EtalabConfig, window.swig));
