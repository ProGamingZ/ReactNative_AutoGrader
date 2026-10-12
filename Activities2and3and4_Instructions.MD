# Activities 2, 3, and 4 Instructions

The following guidelines are based on the reference file "Activities2and3and4_Instructions.txt"[cite: 1].

## Activity 2
*   **Objective:** Create one static, single-page UI using React Native (JavaScript or TypeScript)[cite: 1]. 
*   **Options:** You may create any page, such as a Profile, Dashboard, Market, Discovery, Home, or Settings page[cite: 1].
*   **Focus:** Focus on the UI design and layout[cite: 1]. No backend or API functionality is required[cite: 1].
*   **Submission Requirements:**
    *   Upload only the files you created or edited for your page[cite: 1].
    *   Do not upload the entire React Native project or unrelated files[cite: 1].
    *   Include all files needed for your page to work[cite: 1].
    *   *Example:* If your Dashboard uses App.js, Dashboard.tsx, DashboardLogic.tsx, and Dashboard.ts, upload those files only[cite: 1].

---

## Activity 3
*   **Objective:** Create an interactive, single-page application that renders a dynamic list using React Native (JavaScript or TypeScript)[cite: 1].
*   **Options:** You may create any type of list app, such as a To-Do List, Grocery Tracker, Contact Book, Movie Wishlist, or Inventory Manager[cite: 1].
*   **Required Features:**
    *   A `<TextInput>` to allow users to type a new item[cite: 1].
    *   A touchable component (e.g., `<TouchableOpacity>`) to add the typed item to your list[cite: 1].
    *   A `<FlatList>` to efficiently display the added items[cite: 1].
    *   A way to interact with the list items (e.g., a "Delete" button on each row, or tap to mark as complete)[cite: 1].
    *   The `useState` hook to manage the list data and the current input text[cite: 1].
*   **Focus:** Focus on state management, interactivity, and UI layout[cite: 1]. No backend, database, or API functionality is required—it is completely expected that your list will reset to empty if the app reloads[cite: 1].
*   **Submission Requirements:**
    *   Upload only the files you created or edited for your page[cite: 1].
    *   Do not upload the entire React Native project (e.g., do not include node_modules)[cite: 1].
    *   Include all files needed for your page to work[cite: 1].
    *   *Example:* If your Grocery App uses App.js, GroceryList.jsx, and globalStyles.js, upload those files only[cite: 1].

---

## Activity 4
*   **Objective:** Create a basic multi-screen application using React Navigation (JavaScript or TypeScript)[cite: 1].
*   **Options:** You may create any type of app that requires moving between pages, such as an E-commerce Catalog, Employee Directory, Recipe Book, or Movie Explorer[cite: 1].
*   **Required Features:**
    *   A `<NavigationContainer>` and a Stack Navigator (`createNativeStackNavigator`) managing your app's routing[cite: 1].
    *   A minimum of 3 distinct screens (e.g., a Home Screen, a Catalog/List Screen, and an Item Details Screen)[cite: 1].
    *   Use `navigation.navigate()` to transition forward between your screens[cite: 1].
    *   Use `navigation.goBack()` on at least one custom button to demonstrate manual reverse navigation[cite: 1].
    *   Pass parameters/data between screens using `route.params` (e.g., tapping a specific product on the Catalog screen passes its name, price, and description to the Details screen)[cite: 1].
*   **Focus:** Focus on routing flow, screen transitions, and successfully passing data objects[cite: 1]. No backend, database, or API functionality is required—it is completely expected that you will use hardcoded mock data (like a standard JavaScript array of objects) to supply the data passed between your screens[cite: 1].
*   **Submission Requirements:**
    *   Upload only the files you created or edited for your app[cite: 1].
    *   Do not upload the entire React Native project (e.g., do not include node_modules)[cite: 1].
    *   Include all files needed for your navigation flow to work[cite: 1].
    *   *Example:* If your Store App uses App.js, HomeScreen.js, ProductList.js, ProductDetails.js, and globalStyles.js, upload those files only[cite: 1].