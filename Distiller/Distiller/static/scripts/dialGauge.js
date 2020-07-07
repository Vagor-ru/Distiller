// JavaScript source code
//console.log('Попали в сценарий DialGauge.js');

/**
 * Создает стрелочный прибор для отображения какого-либо значения.
 **/
class DialGauge extends EventTarget {
    /*наследование от EventTarget необходимо для создания клиентских событий,
      чтобы можно было использовать addEventListener объекта этого класса
      а в edge то и не работает...*/

    //static Parameters;

    /**
    * Объект, содержащий все атрибуты
    * стрелочного прибора
    */
    Attributes = {
    id: '',
    height: 100,
    units: '',
    title: '',
    value: 0,
    minValue: 0,
    maxValue: 100,
    majorTicks: 10,
    minorTicks: 2,
    canBeChanged: false,
};

    /**
     * Конструктор объекта стрелочного прибора
     * @param {any} Attributes  -параметры стрелочного прибора
     */
    constructor(Attributes) {
        super();    //конструктор родителя EventTarget
        //Если нет аргумента-объекта, выбросить исключение
        if (typeof (Attributes) === 'undefined') { throw new ReferenceError("Arguments are required");}
        //console.log("Создается экземпляр стрелкового прибора");

        //если в Attributes отсутствует id либо он не задан, выбросить исключение
        if (!('id' in Attributes) || Attributes["id"] === 'undefined' || Attributes["id"].trim() === "") {
            //console.log("Сейчас выкину исключение");
            throw new ReferenceError("Required id attribute not defined.");
        }
        else {
            //console.log(Attributes.id + '=>' + this.Attributes.id);
            this.Attributes.id = Attributes.id; //сохранить id  стрелочного показометра
        }

        this.SVG_NS = "http:\/\/www.w3.org/2000/svg"; //пространство имен SVG (name space)
        this.rad = Math.PI / 180;    //перевод градусов в радианы

        this.Contaner;  //div, в котором отрисовывается прибор
        this.DivSVG;    //контейнер для SVG
        this.SVG;       //SVG-объект
        this.DivInput;   //div, в котором отображается маленький экран со значением отображаемого параметра
        this.InputValue; //поле ввода и отображения значения 
        this.Needle;     //объект svg poligon (стрелка в виде треугольника)

        //проверить остальные входные параметры
        for (let attr in Attributes) {
            switch (attr) {
                case 'height':
                    if (typeof (Attributes.height) == 'number') {
                        this.Attributes.height = Attributes.height < 10 ? 10 : Attributes.height;
                    }
                    else { console.warn('Type of height must be a number'); }
                    break;
                case 'units':
                    if (typeof (Attributes.units) == 'string') { this.Attributes.units = Attributes.units; }
                    else { console.warn('Type of units must be a string'); }
                    break;
                case 'title':
                    if (typeof (Attributes.title) == 'string') { this.Attributes.title = Attributes.title; }
                    else { console.warn('Type of title must be a string'); }
                    break;
                case 'value':
                    if (typeof (Attributes.value) == 'number') { this.Attributes.value = Attributes.value; }
                    else { console.warn('Type of value must be a number'); }
                    break;
                case 'minValue':
                    if (typeof (Attributes.minValue) == 'number') {
                        this.Attributes.minValue = Attributes.minValue;
                    }
                    else { console.warn('Type of minValue must be a number'); }
                    break;
                case 'maxValue':
                    if (typeof (Attributes.maxValue) == 'number') {
                        this.Attributes.maxValue = Attributes.maxValue;
                    }
                    else { console.warn('Type of maxValue must be a number'); }
                    break;
                case 'majorTicks':
                    if (typeof (Attributes.majorTicks) == 'number') {
                        this.Attributes.majorTicks = Attributes.majorTicks;
                    }
                    else { console.warn('Type of majorTicks must be a number'); }
                    break;
                case 'minorTicks':
                    if (typeof (Attributes.minorTicks) == 'number') {
                        this.Attributes.minorTicks = Attributes.minorTicks;
                    }
                    else { console.warn('Type of minorTicks must be a number'); }
                    break;
                case 'canBeChanged':
                    this.Attributes.canBeChanged = (Attributes.canBeChanged) ? true : false;
                    break;
            }
        }
        this.draw();
        //если gauges коллекция ещё не создана, создать ея
        if (!('gauges' in document)) { document.gauges = {}; }
        document.gauges[this.Attributes.id] = this;

    }

    /**
     * отрисовывает стрелочный прибор на странице
     **/
    draw() {
        //Подготовка контейнера div
        let upContaner = document.querySelector(`[id="${this.Attributes.id}"]`);
        //console.log(upContaner);
        if (upContaner === null) {
            //console.log("Создание контейнера прибора");
            upContaner = document.createElement("div");
            document.querySelector("body").appendChild(upContaner);
            upContaner.setAttribute('id', `${this.Attributes.id}`);
        }
        else {
            //зачистить контейнер
            while (upContaner.firstChild) { upContaner.removeChild(upContaner.firstChild); }
        }
        this.Contaner = document.createElement('div');
        upContaner.appendChild(this.Contaner);
        this.Contaner.style.cssText = `
            border-left : 3px solid #EAEAEA; border-top : 3px solid #EAEAEA;
            border-bottom : 3px solid #5F5F5F; border-right : 3px solid #5F5F5F;
            border-radius : 4px;
            background-color : lightgray;
            display : inline-block;
                                        `;
        //this.Contaner.textContent = `Это контейнер прибора ${this.Contaner.id}`;

        //Создание div для стрелочного прибора
        this.DivSVG = document.createElement("div");
        this.DivSVG.style.cssText = `
            border-left : 3px solid #5F5F5F; border-top : 3px solid #5F5F5F;
            border-bottom : 3px solid #EAEAEA; border-right : 3px solid #EAEAEA;
            border-radius : 4px;
            background-color : white;
                                    `;
        this.Contaner.appendChild(this.DivSVG);

        //Создание div для маленького экрана под прибором
        this.DivInput = document.createElement("div");
        this.Contaner.appendChild(this.DivInput);

        //Создание поля ввода и отображения значения
        this.InputValue = document.createElement("input");
        this.InputValue.style.cssText = `
            width : 3em ;
            background-color : gray;
            margin : 3px auto 3px auto;
            text-align : center;
            font : ${this.Attributes.height / 10}px verdana, sans-serif;
            font-weight : 600;
            display : block;
                                        `;
        this.InputValue.value = this.Attributes.value;
        //ivs.disabled = !this.Attributes.canBeChanged;
        if (!this.Attributes.canBeChanged) {
            this.InputValue.setAttribute("readonly", "true");
        }
        this.DivInput.appendChild(this.InputValue);
        //действия при вводе в поле инпут (через стрелочную функцию, не имеющую своего this)
        this.InputValue.addEventListener("change", () => {
            let val = (this.InputValue.value);
            //console.log(typeof (_this.Attributes.minValue));
            if (!isNaN(val)) {
                val = val < this.Attributes.minValue ? this.Attributes.minValue : val;
                val = val > this.Attributes.maxValue ? this.Attributes.maxValue : val;
                this.Attributes.value = val;
                this.InputValue.value = val;
                this.drawNeedle();
                this.dispatchEvent(new CustomEvent("changeValue", { detail: { id: this.Attributes.id, value: this.Attributes.value } }));
            }
            else { this.InputValue.value = this.Attributes.value; }
        }, false);


        //создание SVG прибора
        this.SVG = document.createElementNS(this.SVG_NS, "svg");
        this.SVG.setAttributeNS(null, "height", this.Attributes.height);
        this.SVG.setAttributeNS(null, "width", this.Attributes.height * 2);
        this.SVG.style.border = "0px";

        //мышинные события в SVG
        this.SVG.onselectstart = () => false;   //исключить выделение
        this.SVG.addEventListener("mousemove", (event) => {
            //console.log(event);
            //console.log(`mousemove: ${event.clientX}:${event.clientY}, which=${event.which}`);
            //если мыха двигается с зажатой левой клавишей, следуем за ёй и пересчитываем value
            if (event.buttons == 1) {
                this.dropNeedle(event);
            }
        }, false);
        this.SVG.addEventListener("mousedown", (event) => {
            this.dropNeedle(event);
        }, false);
        this.SVG.addEventListener("mouseup", (event) => {
            if (this.Attributes.canBeChanged) {
                this.dispatchEvent(new CustomEvent("changeValue", { detail: { value: this.Attributes.value } }));
            }
        }, false);

        this.DivSVG.appendChild(this.SVG);

        //отрисовка шкалы
        this.drawScale();

        //создание и установка стрелки
        this.Needle = document.createElementNS(this.SVG_NS, "polygon");
        this.Needle.style = `fill: red; transition: 1s all`;
        //this.Needle.setAttributeNS(null, "fill", "#000080");
        this.SVG.appendChild(this.Needle);
        this.drawNeedle();
    }

    /**
     * перемещает стрелку в соответствии с позицией курсора мыши
     **/
    dropNeedle(event) {
        if (this.Attributes.canBeChanged) {
            let SVGRect = this.SVG.getBoundingClientRect();
            let cx = SVGRect.left + this.Attributes.height; //центр оси в абсолютных координатах
            let cy = SVGRect.top + this.Attributes.height * (1 - 1 / 50);
            let x = event.clientX - cx;
            let y = event.clientY - cy;
            //console.log(`абсолютные ${event.clientX}:${event.clientY}  относительные ${x}:${y} left:top=${SVGRect.left}:${SVGRect.top}`);
            let angle = Math.atan2(y, x) / this.rad;
            angle = angle > 0 && angle < 90 ? 0 : angle;
            angle = angle > 0 && angle > 90 ? -180 : angle;
            let round = this.Attributes.maxValue < 10 ? 2 : 1;
            this.Attributes.value = (((angle + 180) / 180) * (this.Attributes.maxValue -
                this.Attributes.minValue) + this.Attributes.minValue).toFixed(round);
            //console.log(`угол=${angle}, value=${this.Attributes.value}`);
            this.drawNeedle();
            this.InputValue.value = this.Attributes.value;
        }
    }


    /**
     * Отрисовывает шкалу, включая отметки шкалы и числовые значения отметок
     **/
    drawScale() {
        var cx = this.Attributes.height;                //ось шкалы по x
        var cy = this.Attributes.height * (1 - 1 / 50); //ось шкалы по y
        var r = this.Attributes.height * (1 - 1 / 50 - 1 / 5 - 1 / 5);  //радиус расположения низов отметок шкалы
        var a = r + this.Attributes.height*(1 / 5+1/10);          //большая полуось элипса расположения текстовых отметок
        var b = r + this.Attributes.height * (1 / 5 + 1 / 20);    //малая полуось
        var numberOfDivisions = this.Attributes.majorTicks * this.Attributes.minorTicks;  //количество делений шкалы
        var deviation = 180 / (numberOfDivisions); //шаг деления шкалы в градусах
        var scaleDivision = (this.Attributes.maxValue - this.Attributes.minValue) / (numberOfDivisions);  //значение одного деления
        for (var i = 0; i <= numberOfDivisions; i++) {
            var l = i % this.Attributes.minorTicks == 0 ? this.Attributes.height / 5 : this.Attributes.height / 7;     //длина отметки шкалы
            var angleRad = (i * deviation - 180) * this.rad;   //угол отметки шкалы в радианах
            //координаты начала и конца отметки
            var sx1 = cx + r * Math.cos(angleRad);
            var sy1 = cy + r * Math.sin(angleRad);
            var sx2 = cx + (r + l) * Math.cos(angleRad);
            var sy2 = cy + (r + l) * Math.sin(angleRad);
            var sxT = cx + (a) * Math.cos(angleRad);
            var syT = cy + (b) * Math.sin(angleRad);

            //добавление отметки шкалы
            let scaleLine = document.createElementNS(this.SVG_NS, "line");
            scaleLine.style.stroke = 'black';
            let scaleLineObj = {
                class: "scale",
                x1: sx1,
                y1: sy1,
                x2: sx2,
                y2: sy2
            };
            this.setSVGAttributes(scaleLine, scaleLineObj);
            this.SVG.appendChild(scaleLine);

            //добавление числа отметки шкалы
            if (i % this.Attributes.minorTicks == 0) {
                var scaleText = document.createElementNS(this.SVG_NS, "text");
                scaleText.style = `font: bold ${this.Attributes.height/10}px verdana, sans-serif; text-anchor: middle;`;
                var scaleTextObj = {
                    class: "scale",
                    x: sxT,
                    y: syT,
                };
                this.setSVGAttributes(scaleText, scaleTextObj);
                let round = this.Attributes.maxValue < 10 ? 1 : 0;
                scaleText.textContent = (this.Attributes.minValue + i * scaleDivision).toFixed(round);
                this.SVG.appendChild(scaleText);

            }
        }

        let units = document.createElementNS(this.SVG_NS, "text");
        units.style = `font:bold ${this.Attributes.height/5}px verdana, sans-serif; text-anchor: middle;`;
        let unitsTextAttr = {
            class: "units",
            x: this.Attributes.height,
            y: this.Attributes.height/1.5,
        }
        this.setSVGAttributes(units, unitsTextAttr);
        units.textContent = this.Attributes.units;
        this.SVG.appendChild(units);
    }

    /**
     * перемещает стрелку в нужную позицию
     **/
    drawNeedle() {
        var r = this.Attributes.height * (1 - 2 / 5 + 1 / 6);  //радиус верха стрелки
        var widthNeedle = this.Attributes.height / 50;
        //console.log(`${this.Attributes.id}.value=${this.Attributes.value}`);
        var angle = 180 * ((this.Attributes.value - this.Attributes.minValue) /
            (this.Attributes.maxValue - this.Attributes.minValue)) - 180;    //угол поворота стрелки
        var cx = this.Attributes.height;
        var cy = this.Attributes.height * (1 - 1 / 50); //ось шкалы по y
        //console.log(`r=${r}, angle=${angle}, cx=${cx}, cy=${cy}`);

        var nx1 = cx + (widthNeedle) * Math.cos((angle - 90) * this.rad);
        var ny1 = cy + (widthNeedle) * Math.sin((angle - 90) * this.rad);

        var nx2 = cx + (r) * Math.cos(angle * this.rad);
        var ny2 = cy + (r) * Math.sin(angle * this.rad);

        var nx3 = cx + (widthNeedle) * Math.cos((angle + 90) * this.rad);
        var ny3 = cy + (widthNeedle) * Math.sin((angle + 90) * this.rad);

        //console.log(`${nx1},${ny1} ${nx2},${ny2} ${nx3},${ny3}`)
        var points = nx1 + "," + ny1 + " " + nx2 + "," + ny2 + " " + nx3 + "," + ny3;
        //console.log(points);
        this.Needle.setAttributeNS(null, "points", points);
    }

    /**
     * геттер значения показометра
     **/
    get value() { return this.Attributes.value }

    /**
     * сеттер значения показометра
     **/
    set value(value) {
        if (!NaN) {
            this.Attributes.value = value;
            //console.log(this.Attributes.value);
            if (this.Attributes.value < this.Attributes.minValue) {
                this.Attributes.value = this.Attributes.minValue;
            }
            if (this.Attributes.value > this.Attributes.maxValue) {
                this.Attributes.value = this.Attributes.maxValue;
            }
            //console.log(typeof())
            //console.log(`${this.InputValue.value}=>${this.Attributes.value}`);
            this.InputValue.value = this.Attributes.value;
            this.drawNeedle();
        }
    }

    /**
     * возвращает логическое значение можно или нет менять показания прибора
     **/
    get canBeChanged() { return this.Attributes.canBeChanged; }

    /**
     * разрешает/запрещает изменение показаний прибора вручную
     **/
    set canBeChanged(value) {
        this.Attributes.canBeChanged = value ? true : false;
        if (this.Attributes.canBeChanged) {
            this.InputValue.removeAttribute("readonly");
        }
        else {
            this.InputValue.setAttribute("readonly", "true");
        }
    }


    /**
    * Устанавливает заданные атрибуты в указанной ноде
    * @param elmt   //элемент
    * @param oAtt   //атрибуты
    */
    setSVGAttributes(elmt, oAtt) {
        for (var prop in oAtt) {
            elmt.setAttributeNS(null, prop, oAtt[prop]);
        }
    }


}


class Thermometer extends EventTarget {

    /**
    * Объект, содержащий все атрибуты
    * термометра
    */
    Attributes = {
        id: '',
        width: 300,
        units: '',
        title: '',
        value: 0,
        triggerValue: 100,
        minValue: 0,
        maxValue: 100,
        majorTicks: 10,
        minorTicks: 2,
        canBeChanged: false,
        withTrigger: false,
    };

    static SVG_NS = "http:\/\/www.w3.org/2000/svg"; //пространство имен SVG (name space)

    /**
    * Конструктор объекта термометра
    * @param {any} Attributes  -параметры термометра
    **/
    constructor(Attributes) {
        super();
        //Если нет аргумента-объекта, выбросить исключение
        if (typeof (Attributes) === 'undefined') { throw new ReferenceError("Arguments are required"); }
        //console.log("Создается экземпляр термометра");

        //если в Attributes отсутствует id либо он не задан, выбросить исключение
        if (!('id' in Attributes) || Attributes["id"] === 'undefined' || Attributes["id"].trim() === "") {
            //console.log("Сейчас выкину исключение");
            throw new ReferenceError("Required id attribute not defined.");
        }
        else {
            //console.log(Attributes.id + '=>' + this.Attributes.id);
            this.Attributes.id = Attributes.id; //сохранить id  стрелочного показометра
        }

        this.Container;  //div, в котором отрисовывается термометр
        //this.DivSVG;    //контейнер для SVG
        this.SVG;       //SVG-объект
        this.InputTrigger;   //поле ввода, в котором отображается маленький экран со значением триггера
        this.InputValue; //поле отображения значения температуры
        this.Needle;     //объект svg poligon (стрелка в виде треугольника, показывающая значение триггера)
        this.Bar;       //столбик термометра
        this.conversionFactor; //отношение приращения по оси x к соответствующему приращению value
        this.bx         //смещение начала шкалы по оси x

        //проверить остальные входные параметры
        for (let attr in Attributes) {
            switch (attr) {
                case 'width':
                    if (typeof (Attributes.width) == 'number') {
                        this.Attributes.width = Attributes.width < 30 ? 30 : Attributes.width;
                    }
                    else { console.warn('Type of width must be a number'); }
                    break;
                case 'units':
                    if (typeof (Attributes.units) == 'string') { this.Attributes.units = Attributes.units; }
                    else { console.warn('Type of units must be a string'); }
                    break;
                case 'title':
                    if (typeof (Attributes.title) == 'string') { this.Attributes.title = Attributes.title; }
                    else { console.warn('Type of title must be a string'); }
                    break;
                case 'value':
                    if (typeof (Attributes.value) == 'number') { this.Attributes.value = Attributes.value; }
                    else { console.warn('Type of value must be a number'); }
                    break;
                case 'triggerValue':
                    if (typeof (Attributes.triggerValue) == 'number') { this.Attributes.triggerValue = Attributes.triggerValue; }
                    else { console.warn('Type of value must be a number'); }
                    break;
                case 'minValue':
                    if (typeof (Attributes.minValue) == 'number') {
                        this.Attributes.minValue = Attributes.minValue;
                    }
                    else { console.warn('Type of minValue must be a number'); }
                    break;
                case 'maxValue':
                    if (typeof (Attributes.maxValue) == 'number') {
                        this.Attributes.maxValue = Attributes.maxValue;
                    }
                    else { console.warn('Type of maxValue must be a number'); }
                    break;
                case 'majorTicks':
                    if (typeof (Attributes.majorTicks) == 'number') {
                        this.Attributes.majorTicks = Attributes.majorTicks;
                    }
                    else { console.warn('Type of majorTicks must be a number'); }
                    break;
                case 'minorTicks':
                    if (typeof (Attributes.minorTicks) == 'number') {
                        this.Attributes.minorTicks = Attributes.minorTicks;
                    }
                    else { console.warn('Type of minorTicks must be a number'); }
                    break;
                case 'withTrigger':
                    this.Attributes.withTrigger = Boolean(Attributes.withTrigger);
                    break;
            }
        }
        this.draw();
        //если gauges коллекция ещё не создана, создать ея
        if (!('gauges' in document)) { document.gauges = {}; }
        document.gauges[this.Attributes.id] = this;

    }

    /**
     * отрисовывает термометр
     **/
    draw() {
        //Подготовка контейнера div
        let upContainer = document.querySelector(`[id="${this.Attributes.id}"]`);
        //console.log(this.Contaner);
        if (upContainer === null) {
            //console.log("Создание контейнера прибора");
            upContainer = document.createElement("div");
            document.querySelector("body").appendChild(upContainer);
            upContainer.setAttribute('id', `${this.Attributes.id}`);
        }
        else {
            //зачистить контейнер
            while (upContainer.firstChild) { upContainer.removeChild(upContainer.firstChild); }
        }
        //console.log(upContainer);
        this.Container = document.createElement('div');
        upContainer.appendChild(this.Container);
        this.Container.style.cssText = `
            border-left : 3px solid #EAEAEA; border-top : 3px solid #EAEAEA;
            border-bottom : 3px solid #5F5F5F; border-right : 3px solid #5F5F5F;
            border-radius : 4px;
            background-color : lightgray;
            display: -webkit-inline-flex; -webkit-justify-content: flex-start; -webkit-align-items: center;
            display: inline-flex; justify-content: flex-start;align-items: center;
                                        `;
        //this.Container.textContent = `Это контейнер прибора ${this.Contaner.id}`;

        //Создание div для маленьких экранов слева
        let divDisplays = document.createElement("div");
        divDisplays.style.cssText = `
            display:inline-block;
            font : ${this.Attributes.width/22}px verdana, sans-serif;
            font-weight : 500;
                                    `;
        //divDisplays.style.display = "inline-block";
        this.Container.appendChild(divDisplays);

        //вид инпутов
        let cssInput = `width : 4em;
            background-color : gray;
            border-left : 3px solid DimGray; border-top : 3px solid DimGray;
            border-bottom : 3px solid WhiteSmoke; border-right : 3px solid WhiteSmoke;
            /*margin : 3px auto 3px auto;*/
            font : ${this.Attributes.width / 22}px verdana, sans-serif;
            font-weight : 700;
            text-align : right;
            margin-left: 3px;
            /*margin-top:auto; margin-bottom:auto;*/
            /*display : block*/`;

        //если установлено, добавить экран триггера
        //console.log(this.Attributes.withTrigger);
        if (this.Attributes.withTrigger) {
            let divTrigger = document.createElement("div");
            divDisplays.appendChild(divTrigger);
            this.inputTrigger = document.createElement("input");
            this.inputTrigger.style.cssText = cssInput;
            this.inputTrigger.type = "number";
            divTrigger.appendChild(this.inputTrigger);
            this.inputTrigger.value = this.Attributes.triggerValue;
            this.inputTrigger.insertAdjacentText("afterend", this.Attributes.units);
            //добавить слушателя события "change" на инпуте
            //console.log(this.inputTrigger);
            this.inputTrigger.addEventListener("change", () => {
                let val = (this.inputTrigger.value);
                //console.log(typeof (_this.Attributes.minValue));
                if (!isNaN(val)) {
                    val = val < this.Attributes.minValue ? this.Attributes.minValue : val;
                    val = val > this.Attributes.maxValue ? this.Attributes.maxValue : val;
                    this.Attributes.triggerValue = val;
                    this.inputTrigger.value = val;
                    //console.log(this.inputTrigger);
                    this.drawNeedle();
                    this.dispatchEvent(new CustomEvent("changeTrigger", { detail: { id: this.Attributes.id, value: this.Attributes.triggerValue } }));
                }
                else { this.InputValue.value = this.Attributes.value; }

            }, false);
        }

        //добавить экран температуры
        let divTemperature = document.createElement("div");
        divDisplays.appendChild(divTemperature);
        this.InputValue = document.createElement("input");
        this.InputValue.style.cssText = cssInput;
        this.InputValue.type = "number";
        this.InputValue.setAttribute("readonly", "true");
        divTemperature.appendChild(this.InputValue);
        this.InputValue.value = this.Attributes.value;
        this.InputValue.insertAdjacentText("afterend", this.Attributes.units);

        //создание div для шкалы термометра
        let divSVG = document.createElement("div");
        divSVG.style.cssText = `
            /*border-left : 3px solid #5F5F5F; border-top : 3px solid #5F5F5F;
            border-bottom : 3px solid #EAEAEA; border-right : 3px solid #EAEAEA;
            border-radius : 4px;*/
            background-color : white;
            margin-left:4px;
            margin-right:4px
            /*display: inline-block*/
                                    `;
        this.Container.appendChild(divSVG);

        //создание SVG термометра
        this.SVG = document.createElementNS(Thermometer.SVG_NS, "svg");
        //console.log(this.SVG);
        this.SVG.setAttributeNS(null, "height", this.Attributes.width/7);
        this.SVG.setAttributeNS(null, "width", this.Attributes.width);
        this.SVG.style.border = "0px";
        //мышинные события в SVG
        this.SVG.onselectstart = () => false;   //исключить выделение
        if (this.Attributes.withTrigger) {
            this.SVG.addEventListener("mousemove", (event) => {
                //console.log(event);
                //console.log(`mousemove: ${event.clientX}:${event.clientY}, which=${event.which}`);
                //если мыха двигается с зажатой левой клавишей, следуем за ёй и пересчитываем valueTrigger
                if (event.buttons == 1) {
                    this.dropNeedle(event);
                }
            }, false);
            this.SVG.addEventListener("mousedown", (event) => {
                this.dropNeedle(event);
            }, false);
            this.SVG.addEventListener("mouseup", (event) => {
                this.dispatchEvent(new CustomEvent("changeTrigger", { detail: { value: this.Attributes.triggerValue } }));
            }, false);

        }


        //отрисовка шкалы
        this.drawScale();
        divSVG.appendChild(this.SVG);

    }

    /**
     * перемещает индекс триггера
     * @param {any} event
     */
    dropNeedle(event) {
        let SVGRect = this.SVG.getBoundingClientRect();
        let x = event.clientX - this.bx - SVGRect.left;
        let val = (x / this.conversionFactor + this.Attributes.minValue).toFixed(1);
        val = val < this.Attributes.minValue ? this.Attributes.minValue : val;
        val = val > this.Attributes.maxValue ? this.Attributes.maxValue : val;
        this.Attributes.triggerValue = val;
        this.inputTrigger.value = this.Attributes.triggerValue;
        this.drawNeedle();
    }

    /**
     * рисует шкалу в SVG
     **/
    drawScale() {
        let height = this.Attributes.width / 6;
        let bx = height / 8;
        let by = height;
        let ex = this.Attributes.width - height/4;
        let numberOfDivisions = this.Attributes.majorTicks * this.Attributes.minorTicks;  //количество делений шкалы
        let scaleStep = (ex - bx) / numberOfDivisions; //шаг деления
        let scaleDivision = (this.Attributes.maxValue - this.Attributes.minValue) / (numberOfDivisions);  //значение одного деления
        this.conversionFactor = scaleStep / scaleDivision;  //коэффициент преобразования
        this.bx = bx;
        //console.log(`bx=${bx} by=${by} ex=${ex} numberOfDivisions=${numberOfDivisions} scaleStep=${scaleStep} scaleDivision=${scaleDivision}`);
        for (let i = 0; i <= numberOfDivisions; i++) {
            let l = i % this.Attributes.minorTicks == 0 ? height / 2.2 : height/2.4;
            //console.log(`l=${l}`);
            //добавление отметки шкалы
            let scaleLine = document.createElementNS(Thermometer.SVG_NS, "line");
            scaleLine.style.stroke = 'black';
            let scaleLineObj = {
                class: "scale",
                x1: i * scaleStep+bx,
                y1: by,
                x2: i * scaleStep+bx,
                y2: by-l,
            };
            this.setSVGAttributes(scaleLine, scaleLineObj);
            this.SVG.appendChild(scaleLine);

            //добавление числа отметки шкалы
            if (i % this.Attributes.minorTicks == 0) {
                let scaleText = document.createElementNS(Thermometer.SVG_NS, "text");
                scaleText.style = `font: bold ${this.Attributes.width / 30}px verdana, sans-serif; text-anchor: middle;`;
                let scaleTextObj = {
                    class: "scale",
                    x: i * scaleStep + bx,
                    y: by - l - this.Attributes.width/8/8,
                };
                this.setSVGAttributes(scaleText, scaleTextObj);
                let round = this.Attributes.maxValue < 10 ? 1 : 0;
                scaleText.textContent = (this.Attributes.minValue + i * scaleDivision).toFixed(round);
                this.SVG.appendChild(scaleText);

            }

        }
        //добавление названия термометра
        let titleText = document.createElementNS(Thermometer.SVG_NS, "text");
        titleText.style = `font: ${this.Attributes.width / 24}px verdana, sans-serif;text-anchor: start; fill: #1e3c1e; stroke: #1e3c1e;/*stroke:#000080;*/`;
        let titleTextObj = {
            class: "scale",
            x: bx,
            y: height / 4.3,
        };
        this.setSVGAttributes(titleText, titleTextObj);
        titleText.textContent = this.Attributes.title;
        this.SVG.appendChild(titleText);

        //создание и отрисовка столбика термометра
        let defs = document.createElementNS(Thermometer.SVG_NS, "defs");
        defs.innerHTML = `    <filter id="Shadow" x="0" y="0" >
      <feOffset result="offOut" in="SourceGraphic" dx="2" dy="2"/>
      <feGaussianBlur result="blurOut" in="offOut" stdDeviation="4"/>
      <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
    </filter>
    <linearGradient id="Bar" x1="0" y1="1" x2="0" y2="0" spreadMethod="pad">
      <stop stop-color="#ff0000" offset="0%"/>
      <stop stop-color="#f9a7a7" offset="60%"/>
      <stop stop-color="#ff0000" offset="100%"/>
    </linearGradient>
        `;
        this.SVG.appendChild(defs);
        this.Bar = document.createElementNS(Thermometer.SVG_NS, "rect");
        this.Bar.style = `fill : url(#Bar); filter:url(#Shadow); opacity : 0.7`;
        let barAttr = {
            class: "bar",
            x: bx,
            y: by * (1 - 1 / 20) - height / 2.8,
            height: height / 4.1,
            width: this.Attributes.value * this.conversionFactor,
        };
        this.setSVGAttributes(this.Bar, barAttr);
        //console.log(this.Bar);
        this.SVG.appendChild(this.Bar);

        //создание и отрисовка триггерного указателя
        if (this.Attributes.withTrigger) {
            this.Needle = document.createElementNS(Thermometer.SVG_NS, "polygon");
            this.Needle.style = `fill: #000080; `;
            this.SVG.appendChild(this.Needle);
            this.drawNeedle();
        }
    }

    /**
     * рисует индекс триггера
     * */
    drawNeedle() {
        let height = this.Attributes.width / 6;

        let nx1 = this.bx + this.Attributes.triggerValue * this.conversionFactor;
        let ny1 = height*(1-1 / 2.4);

        let nx2 = nx1 - height/10;
        let ny2 = height;

        let nx3 = nx1 + height / 10;
        let ny3 = height;

        //console.log(`${nx1},${ny1} ${nx2},${ny2} ${nx3},${ny3}`)
        let points = nx1 + "," + ny1 + " " + nx2 + "," + ny2 + " " + nx3 + "," + ny3;
        //console.log(points);
        this.Needle.setAttributeNS(null, "points", points);
    }


    /**
    * Устанавливает заданные атрибуты в указанной svg-ноде
    * @param elmt   //элемент
    * @param oAtt   //атрибуты
    */
    setSVGAttributes(elmt, oAtt) {
        for (var prop in oAtt) {
            elmt.setAttributeNS(null, prop, oAtt[prop]);
        }
    }

    /**
     * 
     **/
    get value() {
        return this.Attributes.value;
    }

    set value(val) {
        if (isNaN(val)) { console.warn("can be number!"); }
        else {
            val = val < this.Attributes.minValue ? this.Attributes.minValue : val;
            val = val > this.Attributes.maxValue ? this.Attributes.maxValue : val;
            this.Attributes.value = val;
            this.InputValue.value = val;
            this.setSVGAttributes(this.Bar, { width: val * this.conversionFactor });
        }
    }

    get triggerValue() {
        return this.Attributes.triggerValue;
    }

    set triggerValue(val) {
        if (isNaN(val)) { console.warn("can be number!"); }
        else {
            val = val < this.Attributes.minValue ? this.Attributes.minValue : val;
            val = val > this.Attributes.maxValue ? this.Attributes.maxValue : val;
            this.Attributes.triggerValue = val;
            this.inputTrigger.value = val;
            this.drawNeedle();
        }
    }

}