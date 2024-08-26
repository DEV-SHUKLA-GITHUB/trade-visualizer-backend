const fs = require('fs');

// Provided JSON data
const mtm_df_json = {
    "columns": ["MTM"],
    "index": ["2024-08-20T09:15:00.000", "2024-08-20T09:16:00.000", "2024-08-20T09:17:00.000"],
    "data": [[100.0], [200.0], [300.0]],
    "minimum_mtm": -300,
    "maximum_mtm": 1500,
    "charges": "100"
};

// Convert the data to the desired format
const data = {};
mtm_df_json.index.forEach((timestamp, i) => {
    const formattedTimestamp = timestamp.replace('T', ' ').replace('.000', '');
    data[formattedTimestamp] = mtm_df_json.data[i][0];
});

const additionalData = {
    "minimum_mtm": mtm_df_json.minimum_mtm,
    "maximum_mtm": mtm_df_json.maximum_mtm,
    "charges": mtm_df_json.charges
};

// Prepare the content for the data.js file
const data_js_content = `const data = ${JSON.stringify(data, null, 4)};
const additionalData = ${JSON.stringify(additionalData, null, 4)};
export {data, additionalData};
`;

// Save the content to a file named data.js
fs.writeFile('data.js', data_js_content, (err) => {
    if (err) throw err;
    console.log('data.js file created successfully!');
});
