import React, { Component } from 'react';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import './App.css';

class App extends Component {
  state = {
    defaultTypography: {
      useNextVariants: true
    },
    lightPallete: {
      type: 'light'
    },
    darkPallete: {
      type: 'dark'
    },
    activeTheme: null,
    lightTheme: true
  };

  onClick() {
    const { lightTheme } = this.state;
    if (lightTheme) {
      const newTheme = createMuiTheme({
        palette: this.state.darkPallete,
        typography: this.state.defaultTypography
      });
    } else {
      const newTheme = createMuiTheme({
        palette: this.state.lightPallete,
        typography: this.state.defaultTypography
      });
    }
    console.log('I was clicked.');
  }

  componentWillMount() {
    this.setState({
      activeTheme: createMuiTheme({
        palette: this.state.darkPallete,
        typography: this.state.defaultTypography
      })
    });
  }

  render() {
    const { activeTheme } = this.state;
    console.log(activeTheme);
    return (
      <MuiThemeProvider theme={activeTheme}>
        <Button variant="contained" color="primary" onClick={this.onClick}>
          Click Me
        </Button>
      </MuiThemeProvider>
    );
  }
}

export default App;
