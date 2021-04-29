import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import Summaries from '../Routes/Summaries';
import TradingMonitor from '../Routes/TradingMonitor';

export default function Router() {
  return (
    <Switch>
      <Route path="/summaries">
        <Summaries />
      </Route>
      <Route path="/trading-monitor">
        <TradingMonitor />
      </Route>
      <Redirect from="*" to="/summaries" />
    </Switch>
  );
}
