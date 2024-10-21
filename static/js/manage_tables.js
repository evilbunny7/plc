let currentTable = 'Mill';
let currentCorrectionData = {};
const movementLogTables = ['Product_Movement_Log', 'Transfer_Movement_Log', 'Stage_Movement_Log'];

// Add event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('table-select').addEventListener('change', function() {
        currentTable = this.value;
        fetchRecords();
        toggleAddRecordButton();
    });

    document.getElementById('add-record-btn').addEventListener('click', function() {
        addNewRow();
    });

    // Initial load
    fetchRecords();
    toggleAddRecordButton();
});

function toggleAddRecordButton() {
    const addRecordBtn = document.getElementById('add-record-btn');
    if (movementLogTables.includes(currentTable)) {
        addRecordBtn.style.display = 'none';
    } else {
        addRecordBtn.style.display = 'block';
    }
}

function fetchRecords() {
    fetch(`/api/${currentTable}`)
        .then(response => response.json())
        .then(records => {
            const thead = document.getElementById('records-header');
            const tbody = document.getElementById('records-body');
            thead.innerHTML = '';
            tbody.innerHTML = '';

            if (movementLogTables.includes(currentTable)) {
                thead.innerHTML = `
                    <tr>
                        <th>Date</th>
                        <th>Mill</th>
                        <th>Shift</th>
                        <th>Miller</th>
                        <th>Product/Transfer/Stage</th>
                        <th>Opening Balance</th>
                        <th>Closing Balance</th>
                        <th>Movement</th>
                        <th>Action</th>
                    </tr>
                `;
                records.forEach(record => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${record.date}</td>
                        <td>${record.mill_name}</td>
                        <td>${record.shift}</td>
                        <td>${record.miller}</td>
                        <td>${record.name}</td>
                        <td>${record.opening_balance}</td>
                        <td>${record.closing_balance}</td>
                        <td>${record.movement}</td>
                        <td><button onclick="openCorrectionModal(${JSON.stringify(record).replace(/"/g, '&quot;')})">Correct</button></td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                thead.innerHTML = `
                    <tr>
                        <th>Name</th>
                        <th>Actions</th>
                    </tr>
                `;
                records.forEach(record => {
                    tbody.appendChild(createRecordRow(record));
                });
            }
        })
        .catch(error => console.error(`Error fetching ${currentTable} records:`, error));
}

function createRecordRow(record) {
    const tr = document.createElement('tr');
    if (record.log_id !== undefined) {
        // This is a movement log record
        tr.innerHTML = `
            <td>${record.name}</td>
            <td>
                <button onclick="openCorrectionModal(${record.log_id}, '${currentTable}', '${record.id_field}', ${record.id}, ${record.mill_id})">Correct</button>
            </td>
        `;
    } else {
        // This is a regular record
        tr.innerHTML = `
            <td>${record.name}</td>
            <td>
                <button onclick="editRecord(this, ${record.id}, '${record.name}')">Edit</button>
                <button onclick="deleteRecord(${record.id})">Delete</button>
            </td>
        `;
    }
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

function openCorrectionModal(record) {
    console.log("Opening correction modal for record:", record);
    currentCorrectionData = {
        log_id: record.log_id,
        table_name: currentTable,
        id_field: record.id_field,
        id_value: record.id,
        mill_id: record.mill_id
    };
    document.getElementById('correctionDetails').innerHTML = `
        Date: ${record.date}<br>
        Mill: ${record.mill_name}<br>
        Product/Transfer/Stage: ${record.name}<br>
        Opening Balance: ${record.opening_balance}<br>
        Current Closing Balance: ${record.closing_balance}<br>
        Current Movement: ${record.movement}
    `;
    document.getElementById('correctionModal').style.display = 'block';
}

function closeCorrectionModal() {
    console.log("Closing correction modal");
    document.getElementById('correctionModal').style.display = 'none';
}

function submitCorrection() {
    console.log("Submitting correction:", currentCorrectionData);
    const newEndValue = document.getElementById('newEndValue').value;
    if (!newEndValue) {
        alert("Please enter a new end value.");
        return;
    }
    currentCorrectionData.new_end_value = parseFloat(newEndValue);

    fetch('/api/correct', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentCorrectionData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Correction applied successfully');
            fetchRecords(); // Refresh the data display
        } else {
            alert('Failed to apply correction: ' + data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred while applying the correction');
    });

    closeCorrectionModal();
}
