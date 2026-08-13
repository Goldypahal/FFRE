import React, { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught UI Error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="min-h-screen flex items-center justify-center bg-background text-on-surface p-6">
          <div className="max-w-md w-full bg-surface-container border border-outline-variant rounded-xl p-6 text-center shadow-lg">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center mx-auto mb-4 text-xl">
              ⚠️
            </div>
            <h2 className="text-xl font-bold mb-2">Something went wrong</h2>
            <p className="text-on-surface-variant text-sm mb-6">
              An unexpected error occurred in the application UI.
            </p>
            <div className="p-3 bg-surface-container-low rounded text-xs font-mono text-rose-400 text-left overflow-auto max-h-32 mb-6 border border-rose-500/20">
              {this.state.error?.message || "Unknown error"}
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-investment-gold text-surface font-semibold rounded hover:opacity-90 transition-all w-full"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
