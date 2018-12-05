import React, { Component } from 'react';
import Topbar from '../components/layout/Topbar';
import Sidebar from '../components/layout/Sidebar';

class App extends Component {
  render() {
    return (
      <div style={{ display: 'flex' }}>
        <Topbar />;
        <Sidebar />;
      </div>
    );
  }
}

export default App;
