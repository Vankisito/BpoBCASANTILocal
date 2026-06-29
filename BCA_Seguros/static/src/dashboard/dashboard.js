/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

/**
 * Tablero de Inicio de BCA Seguros.
 *
 * Solo dibuja: toda cifra llega ya calculada de bca.dashboard.get_dashboard_data()
 * (contrato spec §6). La navegación delega en action_open(), que devuelve el
 * act_window filtrado por dominio desde el backend (DEC-026 / D-12).
 */
export class BcaDashboard extends Component {
    static template = "BCA_Seguros.Dashboard";
    static props = {
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, loading: true });

        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "bca.dashboard",
                "get_dashboard_data",
                []
            );
            this.state.loading = false;
        });
    }

    /** Abre la vista lista filtrada para la cifra clickeada. */
    async open(key) {
        const action = await this.orm.call("bca.dashboard", "action_open", [key]);
        this.action.doAction(action);
    }

    // ----------------------------------------------------------- formateo
    money(value) {
        return new Intl.NumberFormat("es-MX", {
            style: "currency",
            currency: "MXN",
            maximumFractionDigits: 0,
        }).format(value || 0);
    }

    int(value) {
        return new Intl.NumberFormat("es-MX").format(value || 0);
    }

    date(value) {
        if (!value) {
            return "—";
        }
        // Backend entrega "YYYY-MM-DD" o "YYYY-MM-DD HH:MM:SS".
        return value.slice(0, 10);
    }
}

registry.category("actions").add("bca_dashboard", BcaDashboard);
