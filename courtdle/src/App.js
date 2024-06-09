import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const App = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [currentCaseIndex, setCurrentCaseIndex] = useState(0);
  const [casesInfo, setCasesInfo] = useState([]);
  const [selectedParty, setSelectedParty] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [revealConclusion, setRevealConclusion] = useState(false);
  const [overallResults, setOverallResults] = useState([]);
  const [isLandingPage, setIsLandingPage] = useState(true);
  const [isFinalPage, setIsFinalPage] = useState(false);

  useEffect(() => {
    if (!isLandingPage && casesInfo.length === 0) {
      axios.get('http://127.0.0.1:5000/cases_info')
        .then(response => {
          setCasesInfo(response.data);
          setIsLoading(false);
        })
        .catch(error => console.error('Error fetching cases:', error));
    }
  }, [isLandingPage]);

  const handlePartySelection = (party) => {
    setSelectedParty(party);
    axios.post('http://127.0.0.1:5000/check_answer', {
      case_id: casesInfo[currentCaseIndex].case_id,
      user_choice: party
    })
      .then(response => {
        setIsCorrect(response.data.correct === 'Correct');
        setOverallResults([...overallResults, response.data.correct === 'Correct']);
        setShowResult(true);
      })
      .catch(error => console.error('Error checking answer:', error));
  };

  const handleNextCase = () => {
    setSelectedParty(null);
    setShowResult(false);
    setRevealConclusion(false);
    if (currentCaseIndex < casesInfo.length - 1) {
      setCurrentCaseIndex(currentCaseIndex + 1);
    } else {
      setIsFinalPage(true);
    }
  };

  const countdownToMidnight = () => {
    const now = new Date();
    const midnight = new Date();
    midnight.setHours(24, 0, 0, 0);
    return Math.round((midnight - now) / 1000);
  };

  if (isLandingPage) {
    return (
      <div className="landing-page">
        <h1>Welcome to the Courtdle</h1>
        <p>You will be shown 5 Supreme Court cases and need to decide who it was decided in favor of.</p>
        <button onClick={() => setIsLandingPage(false)}>Start</button>
      </div>
    );
  }

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isFinalPage) {
    return (
      <div className="final-page">
        <h1>Quiz Completed</h1>
        <p>You got {overallResults.filter(result => result).length} out of 5 correct.</p>
        <p>Next quiz available in {countdownToMidnight()} seconds.</p>
      </div>
    );
  }

  const currentCase = casesInfo[currentCaseIndex];

  return (
    <div className="case-page">
      <h1>{currentCase.case_name}</h1>
      <h2>Judges</h2>
      <ul>
        {currentCase.judges.map(judge => <li key={judge}>{judge}</li>)}
      </ul>
      <div className="summary-box">
        <h3>Summary</h3>
        <p>{currentCase.summary}</p>
      </div>
      <div className="party-buttons">
        {currentCase.parties.map(party => (
          <button
            key={party}
            onClick={() => handlePartySelection(party)}
            disabled={!!selectedParty}  // Double negation to ensure it is boolean
          >
            {party}
          </button>
        ))}
      </div>
      {showResult && (
        <div className={`result ${isCorrect ? 'correct' : 'incorrect'}`}>
          {isCorrect ? 'Correct!' : 'Incorrect!'}
        </div>
      )}
      {showResult && (
        <div className="conclusion-box">
          <button onClick={() => setRevealConclusion(!revealConclusion)}>
            {revealConclusion ? 'Hide Conclusion' : 'Show Conclusion'}
          </button>
          {console.log(currentCase.conclusion) && revealConclusion && <p>{currentCase.conclusion}</p>}
        </div>
      )}
      {showResult && (
        <button className="next-case-button" onClick={handleNextCase}>
          Next Case
        </button>
      )}
    </div>
  );
};

export default App;
