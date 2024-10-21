let currentTable = 'Mill';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('table-select').addEventListener('change', function() {
        currentTable = this.value;
        fetchRecords();
    });

    document.getElementById('add-record-btn').addEventListener('click', function() {
        addNewRow();
    });

    fetchRecords();
});

function fetchRecords() {
    fetch(`/api/${currentTable}`)
        .then(response => response.json())
        .then(records => {
            const tbody = document.getElementById('records-body');
            tbody.innerHTML = '';
            records.forEach(record => {
                tbody.appendChild(createRecordRow(record));
            });
        })
        .catch(error => console.error(`Error fetching ${currentTable} records:`, error));
}

function createRecordRow(record) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${record.name}</td>
        <td>
            <button onclick="editRecord(this, ${record.id}, '${record.name}')">Edit</button>
            <button onclick="deleteRecord(${record.id})">Delete</button>
        </td>
    `;
    return tr;
}

function addNewRow() {
    const tbody = document.getElementById('records-body');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" placeholder="Enter name"></td>
        <td>
            <button onclick="saveNewRecord(this)">Save</button>
            <button onclick="cancelAdd(this)">Cancel</button>
        </td>
    `;
    tbody.insertBefore(tr, tbody.firstChild);
}

function saveNewRecord(button) {
    const tr = button.closest('tr');
    const name = tr.querySelector('input').value;
    if (!name) {
        alert('Please enter a name');
        return;
    }
    fetch(`/api/${currentTable}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: name }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        fetchRecords();
    })
    .catch(error => console.error(`Error adding ${currentTable} record:`, error));
}

function cancelAdd(button) {
    const tr = button.closest('tr');
    tr.remove();
}

function editRecord(button, id, currentName) {
    const tr = button.closest('tr');
    tr.innerHTML = `
        <td><input type="text" value="${currentName}"></td>
        <td>
            <button onclick="saveEdit(this, ${id})">Save</button>
            <button onclick="cancelEdit(this, ${id}, '${currentName}')">Cancel</button>
        </td>
    `;
}

function saveEdit(button, id) {
    const tr = button.closest('tr');
    const newName = tr.querySelector('input').value;
    if (!newName) {
        alert('Please enter a name');
        return;
    }
    fetch(`/api/${currentTable}/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newName }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        fetchRecords();
    })
    .catch(error => console.error(`Error updating ${currentTable} record:`, error));
}

function cancelEdit(button, id, originalName) {
    const tr = button.closest('tr');
    tr.innerHTML = `
        <td>${originalName}</td>
        <td>
            <button onclick="editRecord(this, ${id}, '${originalName}')">Edit</button>
            <button onclick="deleteRecord(${id})">Delete</button>
        </td>
    `;
}

function deleteRecord(id) {
    if (confirm(`Are you sure you want to delete this ${currentTable}?`)) {
        fetch(`/api/${currentTable}/${id}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            fetchRecords();
        })
        .catch(error => console.error(`Error deleting ${currentTable} record:`, error));
    }
}