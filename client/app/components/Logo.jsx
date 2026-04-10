import React from 'react';
import './Logo.css';

/** @param {{ variant?: 'default' | 'compact' }} props */
const Logo = ({ variant = 'default' }) => {
  const wrapClass =
    variant === 'compact'
      ? 'premium-logo-wrapper premium-logo-wrapper--compact'
      : 'premium-logo-wrapper';
  return (
    <div className={wrapClass}>
      <div className="premium-logo-bubble">
        <img 
          className="premium-logo-img" 
          src="/logo.png" 
          alt="Giani Ji Logo"
        />
      </div>
    </div>
  );
};

export default Logo;
