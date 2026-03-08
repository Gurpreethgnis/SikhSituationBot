import React from 'react';
import './Perspectives.css';

const Perspectives = ({ activePersona, onPersonaChange }) => {
  const personas = [
    { id: 'child', label: 'Child', icon: '👳🏽' },
    { id: 'teen', label: 'Teen', icon: '👳🏽' },
    { id: 'adult', label: 'Adult', icon: '👳🏽‍♂️' }
  ];

  return (
    <div className="perspectives">
      <div className="perspectives__container">
        {personas.map((persona) => (
          <button
            key={persona.id}
            className={`perspectives__btn ${activePersona === persona.id ? 'perspectives__btn--active' : ''}`}
            onClick={() => onPersonaChange(persona.id)}
            aria-pressed={activePersona === persona.id}
          >
            <span className="perspectives__icon" role="img" aria-hidden="true">
              {persona.icon}
            </span>
            <span className="perspectives__label">{persona.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default Perspectives;
