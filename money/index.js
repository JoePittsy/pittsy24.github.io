let runningTotal = 0;
let salary = 0;
let outgoings = [];
let shown = false;

function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }
  

const clearData = () => {
    runningTotal = 0;
    salary = 0;
    outgoings = [];
    shown = false;
    localStorage.clear('runningTotal');
    localStorage.clear('salary');
    localStorage.clear('outgoings');
    
    location.reload(); 
}

const show = () => {
    if (shown) return;
    document.getElementById('hidden').classList.remove('d-none');
    updateFields();
    shown = true;
}

const updateFields = () => {
    salary = parseFloat(document.getElementById('takeHome').value);
    document.getElementById('outTitle').innerText = `Outgoings: £${runningTotal}`;
    document.getElementById('outTotal').value = runningTotal;
    document.getElementById('spending').value = salary - runningTotal;
    console.log(runningTotal);

    localStorage.setItem('runningTotal', runningTotal);
    localStorage.setItem('salary', salary);
    localStorage.setItem('outgoings', JSON.stringify(outgoings));

}

const newItemNode = (htmlString) => {
    var div = document.createElement('div');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
}

const add = () => {
    let name = document.getElementById('name').value;
    let amount = document.getElementById('amount').value;
    let id = uuidv4();

    if (name === '' || amount === '') {
        alert('Please enter a name and amount');
        return;
    }

    if (isNaN(parseFloat(amount))) {
        alert('Please enter a number');
        return;
    }

    outgoings.push({ name: name, amount: amount, id: id });

    runningTotal += parseFloat(amount);
    updateFields();

    document.getElementById('outgoings').append(newItemNode(`<a class="list-group-item  py-3 lh-tight" id=${id}>
    <div class="d-flex w-100 align-items-center justify-content-between">
        <strong class="mb-1">${name}</strong>
        <small>£${amount}</small>
      </div>
    <button type="button" class="btn btn-danger float-end mt-1" onclick="remove(this)">Remove</button>
  </a>`))
    // alert(`${name}: ${amount}`);
};

const setup = (name, amount, id) => {

    updateFields();

    document.getElementById('outgoings').append(newItemNode(`<a class="list-group-item  py-3 lh-tight" id=${id} >
    <div class="d-flex w-100 align-items-center justify-content-between">
        <strong class="mb-1">${name}</strong>
        <small>£${amount}</small>
      </div>
    <button type="button" class="btn btn-danger float-end mt-1" onclick="remove(this)">Remove</button>
  </a>`))
    // alert(`${name}: ${amount}`);
};


const remove = (context) => {
    console.log(context);
    const id = context.parentNode.id;
    // search outgoings for id
    const index = outgoings.findIndex(item => item.id === id);
    // get the amount
    const amount = outgoings[index].amount;
    // remove item from outgoings
    outgoings.splice(index, 1);
    // remove item from DOM
    context.parentNode.remove();
    // update running total
    runningTotal -= parseFloat(amount);

    updateFields();
}


const main = () => {
    runningTotal = parseFloat(localStorage.getItem('runningTotal')) || 0;
    salary = parseFloat(localStorage.getItem('salary')) || 0;
    outgoings = JSON.parse(localStorage.getItem('outgoings')) || [];
    if (salary > 0 || runningTotal > 0 || outgoings.length > 0) {
        for (let i = 0; i < outgoings.length; i++) {
            const element = outgoings[i];
            setup(element.name, element.amount, element.id);
        }
        document.getElementById('takeHome').value = salary;
        show();
        updateFields();
    }

}

document.addEventListener('DOMContentLoaded', (event) => {
    main();

    document.getElementById("add").addEventListener("click", add);
});