/**
 * School Color Theme Configuration
 * Primary Blue: #1f4788 (Dark Academic Blue)
 * Secondary Orange: #FF9500 (Warm Orange)
 * Accent Green: #2ECC71 (Fresh Green)
 * Neutral White: #FFFFFF
 * Light Gray: #F5F7FA (Background)
 */

export const colors = {
    primary: '#1f4788',      // Dark blue
    secondary: '#FF9500',    // Orange
    accent: '#2ECC71',       // Green
    white: '#FFFFFF',
    lightGray: '#F5F7FA',
    darkGray: '#2C3E50',
    border: '#DDD',
    danger: '#E74C3C',
    success: '#27AE60',
    warning: '#F39C12',
};

export const globalStyles = `
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: ${colors.lightGray};
    color: ${colors.darkGray};
    line-height: 1.6;
  }
  
  a {
    color: ${colors.primary};
    text-decoration: none;
  }
  
  a:hover {
    color: ${colors.secondary};
    text-decoration: underline;
  }
  
  button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    border-radius: 4px;
    transition: all 0.3s ease;
  }
  
  input, textarea, select {
    font-family: inherit;
    border-radius: 4px;
    border: 1px solid ${colors.border};
    padding: 0.5rem 0.75rem;
    transition: border-color 0.3s ease;
  }
  
  input:focus, textarea:focus, select:focus {
    outline: none;
    border-color: ${colors.primary};
    box-shadow: 0 0 0 3px rgba(31, 71, 136, 0.1);
  }
`;
