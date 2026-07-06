import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="text-center p-8">
            <p className="text-destructive text-sm mb-2">Something went wrong</p>
            <p className="text-text-dim text-xs mb-4">
              {this.state.error.message}
            </p>
            <button
              onClick={() => { this.setState({ error: null }); }}
              className="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent/80 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
