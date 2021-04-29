import _ from 'lodash';

const SET_MMSTATS = '@Redux/MMStats/SET_MMSTATS';

const DEFAULT_STATE = {
  mmstats: [],
  latestUpdate: new Date().toUTCString(),
};

export default function MMStatsReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_MMSTATS) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setMMStats(str) {
  let payload = DEFAULT_STATE;
  try {
    const obj = JSON.parse(str || '{}');
    if (Array.isArray(obj.data)) {
      payload.mmstats = obj.data;
    }
    if (typeof obj.date === 'string') {
      payload.latestUpdate = obj.date;
    }
  } catch (err) {
    console.error(err);
  }
  return { type: SET_MMSTATS, payload };
}
