document.addEventListener('DOMContentLoaded', function() {
    // General fetch function to populate dropdowns or input fields
    function fetchData(url, containerId, createElementCallback) {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                let container = document.getElementById(containerId);
                if (!container) return;
                container.innerHTML = ""; // Clear existing options/fields

                data.forEach(item => {
                    createElementCallback(container, item);
                });
                checkDropdowns();
            })
            .catch(error => console.error(`Error fetching data from ${url}:`, error));
    }

    // Fetch dropdown data
    fetchData('/api/get_dropdown_1', 'dropdown-1', createDropdownOption);
    fetchData('/api/get_dropdown_2', 'dropdown-2', createDropdownOption);
    fetchData('/api/get_dropdown_3', 'dropdown-3', createDropdownOption);

    // Fetch input field data
    fetchData('/api/get_product_data', 'dynamic-input-fields', createInputField);
    fetchData('/api/get_transfer_data', 'dynamic-input-fields-2', createInputField);
    fetchData('/api/get_water_stage_data', 'dynamic-input-fields-3', createInputField);

    // Function to create dropdown options
    function createDropdownOption(container, item) {
        if (container.children.length === 0) {
            let defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.textContent = "Select an option";
            container.appendChild(defaultOption);
        }

        let option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        container.appendChild(option);
    }

    // Function to create input fields
    function createInputField(container, item) {
        let fieldContainer = document.createElement('div');
        fieldContainer.classList.add('field-container');

        let label = document.createElement('label');
        label.textContent = `${item.name}:`;
        fieldContainer.appendChild(label);

        let input = document.createElement('input');
        input.type = 'number';
        input.name = item.id; // Set input name as the ID to track database reference
        input.placeholder = `Enter ${item.name}`;
        input.min = 0;
        input.disabled = true;
        fieldContainer.appendChild(input);

        container.appendChild(fieldContainer);
    }

    // Event listeners to enable input fields when all dropdowns are selected
    document.getElementById('dropdown-1').addEventListener('change', checkDropdowns);
    document.getElementById('dropdown-2').addEventListener('change', checkDropdowns);
    document.getElementById('dropdown-3').addEventListener('change', checkDropdowns);
    document.getElementById('date-picker').addEventListener('change', checkDropdowns);

    // Function to check if all dropdowns are selected
    function checkDropdowns() {
        let allSelected = ['dropdown-1', 'dropdown-2', 'dropdown-3', 'date-picker']
            .every(id => document.getElementById(id).value);

        document.querySelectorAll('#dynamic-input-fields input, #dynamic-input-fields-2 input, #dynamic-input-fields-3 input')
            .forEach(input => {
                input.disabled = !allSelected;
            });

        // Add or remove red border based on input fields' state
        let centerContainer = document.querySelector('.center-container');
        if (allSelected) {
            centerContainer.classList.remove('inactive-container');
        } else {
            centerContainer.classList.add('inactive-container');
        }
    }

    // Function to handle form submission (create or update)
    async function submitData() {
        let isUpdate = document.getElementById('log-id')?.value; // Use this field to decide between update and create
        let url = isUpdate ? '/api/update' : '/api/submit';

        // Gather dropdown and date values
        let formData = {
            log_id: isUpdate,
            dropdown_1: document.getElementById('dropdown-1').value,
            dropdown_2: document.getElementById('dropdown-2').value,
            dropdown_3: document.getElementById('dropdown-3').value,
            User_Date: document.getElementById('date-picker').value, // Corrected field name to match Python script
            input_values_1: gatherInputValues('#dynamic-input-fields'),
            input_values_2: gatherInputValues('#dynamic-input-fields-2'),
            input_values_3: gatherInputValues('#dynamic-input-fields-3'),
        };

        // Log to verify all fields
        console.log('Submitting form data:', formData);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                alert('Data submitted successfully');
                clearForm();  // Clear the form after successful submission
            } else {
                alert(result.error); // Display the error message in a pop-up
            }
        } catch (error) {
            console.error('Error submitting form data:', error);
            alert('An error occurred while submitting the form, opening balancce cannot be less than closing balance');
        }
    }

    // Function to gather input field values
    function gatherInputValues(containerSelector) {
        let inputs = document.querySelectorAll(`${containerSelector} input`);
        let values = {};
        inputs.forEach(input => {
            if (input.value.trim() !== '') {
                values[input.name] = parseFloat(input.value);
            }
            // If the input is empty, we don't add it to the values object
        });
        return values;
    }

    // Function to clear form input fields and reset their state
    function clearForm() {
        // Clear dropdown selections and date
        document.getElementById('dropdown-1').value = '';
        document.getElementById('dropdown-2').value = '';
        document.getElementById('dropdown-3').value = '';
        document.getElementById('date-picker').value = '';

        // Clear all input fields and disable them
        document.querySelectorAll('#dynamic-input-fields input, #dynamic-input-fields-2 input, #dynamic-input-fields-3 input')
            .forEach(input => {
                input.value = '';
                input.disabled = true;
            });

        // Add red border since input fields are now disabled
        let centerContainer = document.querySelector('.center-container');
        centerContainer.classList.add('inactive-container');
    }

    // Attach event listener to the submit button
    document.getElementById('submit-button').addEventListener('click', submitData);
});
