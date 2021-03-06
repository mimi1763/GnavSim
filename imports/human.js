'use strict';

import Player from './player.js';
import Card from './card.js';

export default class Human extends Player {

	constructor(name, speaker) {
		super(name, speaker);
		this._human = true;
		this._hasKnocked = false;
	}

	get human() { return this._human; }
	get heldCard() { return super.heldCard; }
	get hasKnocked() { return this._hasKnocked; }

	set human(value) { this._human = value; }
	set heldCard(value) {
		super.heldCard = value;
		this.printGotCard(super.heldCard.name);
	}
	 
	reset() {
		this._hasKnocked = false;
	}

	knockOnTable() {
		this._speaker.say (this.name + tools.TXT_KNOCK);
		this._hasKnocked = true;
	}

	requestSwap(toPlayer) {
		this._speaker.say (this.sayTo(toPlayer, 0) + quote(tools.TXT_WANT_TO_SWAP));
	}

	printGotCard(cardName) {
		cardName = cardName || '';
		let card = cardName === '' ? this._heldCard.name : cardName;
		this._speaker.say (`Player ${this.name}, you got the card ${card}.`);
	}

	async testForSwap(obj) {
		if (obj) {
			let text = "Do you want to ";
			if (obj.name == "deck") {
				text += "draw from the deck";
			} else {
				text += `swap cards with ${obj.name}`;
			}

			let callbackFn = (result) => {
				console.log("human ask result: ", result);
				this._speaker.hideNextTurnButton(true);
				obj.result = result ? 'yes' : 'no';
				return result;
			};

			this._speaker.ask(text, 0, callbackFn);

		} else {
			console.log('testForSwap obj is undefined!');
			return false;
		}
	}
}