import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { UncaughtPromiseError } from "@web/core/errors/error_service";

/**
 * Replaces technical access dialogs with guidance users can act on.
 * Other server and client errors must continue through Odoo's handlers.
 *
 * @param {object} env
 * @param {Error} error
 * @param {Error} originalError
 * @returns {boolean}
 */
function bcaAccessErrorHandler(env, error, originalError) {
    if (!(error instanceof UncaughtPromiseError)) {
        return false;
    }
    if (!(originalError instanceof RPCError)) {
        return false;
    }
    if (originalError.exceptionName !== "odoo.exceptions.AccessError") {
        return false;
    }
    // The module also raises AccessError for business guards such as immutable
    // history. Only rewrite ORM permission-denial messages.
    const ormAccessError =
        /doesn't have '(read|write|create|unlink)' access to:|not allowed to access/i;
    if (!ormAccessError.test(originalError.message || "")) {
        return false;
    }

    error.unhandledRejectionEvent.preventDefault();
    env.services.notification.add(
        _t(
            "Tu usuario no tiene permisos suficientes para realizar esta acción " +
                "o consultar esta información. Si consideras que deberías tener " +
                "acceso, solicita al administrador que revise tu rol."
        ),
        {
            title: _t("Acceso restringido"),
            type: "warning",
            sticky: true,
        }
    );
    return true;
}

registry.category("error_handlers").add("bcaAccessErrorHandler", bcaAccessErrorHandler, {
    sequence: 96,
});
