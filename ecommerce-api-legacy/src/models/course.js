'use strict';

/**
 * Curso da plataforma.
 *
 * Entidade imutável: o preço cobrado no checkout vem daqui, nunca do payload da
 * requisição — o código original já lia `course.price` do banco e esse
 * comportamento foi mantido, já que aceitar valor do cliente permitiria comprar
 * um curso pelo preço que o cliente quisesse.
 */
class Course {
    constructor({ id, title, price, active }) {
        this.id = id;
        this.title = title;
        this.price = price;
        this.active = Boolean(active);
        Object.freeze(this);
    }

    static fromRow(row) {
        return row ? new Course(row) : null;
    }

    /** Invariante de domínio: curso inativo não pode ser comprado. */
    get isPurchasable() {
        return this.active;
    }
}

module.exports = { Course };
