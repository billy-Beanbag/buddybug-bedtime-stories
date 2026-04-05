from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PublicDomainClassicEntry:
    title: str
    source_author: str
    source_url: str
    source_origin_notes: str
    source_text: str


PUBLIC_DOMAIN_CLASSICS: list[PublicDomainClassicEntry] = [
    PublicDomainClassicEntry(
        title="The Story of the Three Bears (1839)",
        source_author="Unknown author (1839 edition)",
        source_url="https://en.wikisource.org/wiki/The_Story_of_the_Three_Bears_(1839)",
        source_origin_notes="Downloaded from Wikisource. Public-domain source text prepared for internal Buddybug Classics import.",
        source_text="""Three Bears, once on a time, did dwell
Snug in a house together,
Which was their own, and suited well
By keeping out the weather.

'Twas seated in a shady wood,
In which they daily walk'd,
And afterwards, as in the mood,
They smok'd and read, or talk'd.

One of them was a great huge Bear,
And one of a middle size,
The other a little, small, wee Bear,
With small red twinkling eyes.

These Bears, each had a porridge-pot,
From which they used to feed;
The great huge Bear's own porridge-pot
Was very large indeed.

A pot of a middle-size the Bear
Of a middle-size had got,
And so the little, small, wee Bear,
A little, small, wee pot.

A chair there was for every Bear,
When they might choose to sit;
The huge Bear had a great huge chair,
And filled it every bit.

The middle Bear a chair had he
Of a middle-size and neat;
The Bear so little, small, and wee
A little, small, wee seat.

They, also, each one had a bed
To sleep upon at night:
The huge Bear's was a great, huge bed,
In length, and width, and height.

The middle Bear laid down his head
On a bed of middle-size;
The wee Bear on a small, wee bed
Did nightly close his eyes.

One morn their porridge being made
And pour'd into each pot,
To taste it they were all afraid
It seem'd so boiling hot.

They, therefore, let their breakfast be
Till it should cooler grow -
And meantime for a walk the three
Into the wood did go.

And now a little old woman there
Came, whilst the Bears were out;
Through window, keyhole, everywhere,
She peep'd and peer'd about:

And then she lifted up the latch
And through the door she went,
For hold of all she could to snatch
No doubt was her intent.

The little old Dame had entered in,
And was well pleased to find
The porridge-pots, and that within
They held food of such kind.

So quickly of a spoon laid hold
The porridge to dip in.
And first out of the great Bear's pot
The porridge she did taste,

Which proving to be very hot
She spat it out in haste.
The middle Bear's she tasted next,
Which being rather cold,

She disappointed was, and vex'd.
But now to where the small, wee Bear
Had left his small, wee cup
She came, and soon the porridge there
By her was eaten up.

Then down the little old woman sat
Within the huge Bear's chair,
But much too hard for her was that,
And so she staid not there.

Next she tried the middle-sized one
And that too soft she found;
Then sat the small, wee chair upon,
Which fitted her all round.

Now here for sometime sat the Dame
Till half inclined to snore,
When out this wee chair's bottom came
And her's came to the floor.

Then went up-stairs,
And poked her ugly head into
The bed-room of the Bears.

And down upon the huge Bear's bed
She lay, which was too high
To suit her little ugly head,
Which easy could not lie.

Then to the middle Bear's she goes
And quick upon it got,
But at the foot too high it rose,
And so she liked it not.

Now down upon the small wee bed
She lay, and it was quite
The thing, both at the foot and head,
And fitted her just right.

Thus finding that it suited well
Within the clothes she crept;
Then into a slumber fell
And snug and soundly slept.

The three Bears in their jackets rough
Now came in from the wood,
Thinking their porridge long enough
To cool itself had stood.

"Somebody has at my porridge been!"
The huge Bear's gruff voice cried;
For there the spoon was sticking in,
Which he left at the side.

"Somebody has at my porridge been!"
Then said the middle Bear,
For also in his pot was seen
The spoon, which made him stare.

The small Bear's small voice said, as in
He peer'd to his wee cup,
"Somebody has at my porridge been,
And eaten it all up!"

On this the three Bears finding that
The while they had been out,
Some one the door had entered at
Began to look about.

"Somebody in my chair has sat!"
With voice so gruff and great
The huge Bear said, when he saw that
His cushion was not straight.

"Somebody in my chair has been!"
The middle Bear exclaim'd;
Seeing the cushion dinted in
By what may not be named.

Then said the little, small, wee Bear,
Looking his chair into,
"Some one's been sitting in my chair,
And sat the bottom through!"

Thought it just as well to go
And do the same up-stairs.

"Some one's been lying in my bed!"
Cried out the great huge Bear,
Who left his pillow at the head
And now it was not there.

"Some one's been lying in my bed!"
The middle Bear then cried,
For it was tumbled at the head
And at the foot and side.

And now the little wee Bear said
With voice both small and shrill,
"Some one's been lying in my bed -
And here she's lying still!"

The other Bears look'd at the bed,
And on the pillow-case
They saw her little dirty head
And little ugly face.

The little old woman had the deep
Voice of the huge Bear heard,
But she was in so sound a sleep
She neither woke nor stirr'd.

And she had heard the middle Bear,
Whose middle voice did seem
To her asleep, as though it were
The voice but of a dream.

But when the small, wee Bear did speak,
She started up in bed,
His voice it was so shrill, the squeak
Shot through her ugly head.

She rubb'd her eyes, and when she saw
The three bears at her side,
She sprang full quick upon the floor -
And then with hop and stride
She to the open window flew.

She lept out with a sudden bound,
And whether in her fall
She broke her neck upon the ground,
Or was not hurt at all,
Or whether to the wood she fled
And 'mongst the trees was lost,
Or found a path which straightway led
To where the highways cross'd,
Remains an untold tale.

THE END.""",
    ),
    PublicDomainClassicEntry(
        title="Little Red Riding-Hood",
        source_author="Charles Perrault via The Blue Fairy Book",
        source_url="https://en.wikisource.org/wiki/The_Blue_Fairy_Book/Little_Red_Riding_Hood",
        source_origin_notes="Downloaded from Wikisource. Public-domain source text prepared for internal Buddybug Classics import.",
        source_text="""Once upon a time there lived in a certain village a little country girl, the prettiest creature was ever seen. Her mother was excessively fond of her; and her grandmother doted on her still more. This good woman got made for her a little red riding-hood; which became the girl so extremely well that everybody called her Little Red Riding-Hood.

One day her mother, having made some custards, said to her:

'Go, my dear, and see how thy grandmamma does, for I hear she has been very ill; carry her a custard, and this little pot of butter.'

Little Red Riding-Hood set out immediately to go to her grandmother, who lived in another village.

As she was going through the wood, she met with Gaffer Wolf, who had a very great mind to eat her up, but he durst not, because of some faggot-makers hard by in the forest. He asked her whither she was going. The poor child, who did not know that it was dangerous to stay and hear a wolf talk, said to him:

'I am going to see my grandmamma and carry her a custard and a little pot of butter from my mamma.'

'Does she live far off?' said the Wolf.

'Oh! ay,' answered Little Red Riding-Hood; 'it is beyond that mill you see there, at the first house in the village.'

'Well,' said the Wolf, 'and I'll go and see her too. I'll go this way and go you that, and we shall see who will be there soonest.'

The Wolf began to run as fast as he could, taking the nearest way, and the little girl went by that farthest about, diverting herself in gathering nuts, running after butterflies, and making nosegays of such little flowers as she met with.

The Wolf was not long before he got to the old woman's house. He knocked at the door - tap, tap.

'Who's there?'

'Your grandchild, Little Red Riding-Hood,' replied the Wolf, counterfeiting her voice; 'who has brought you a custard and a little pot of butter sent you by mamma.'

The good grandmother, who was in bed, because she was somewhat ill, cried out:

'Pull the bobbin, and the latch will go up.'

The Wolf pulled the bobbin, and the door opened, and then presently he fell upon the good woman and ate her up in a moment, for it was above three days that he had not touched a bit. He then shut the door and went into the grandmother's bed, expecting Little Red Riding-Hood, who came some time afterwards and knocked at the door - tap, tap.

'Who's there?'

Little Red Riding-Hood, hearing the big voice of the Wolf, was at first afraid; but believing her grandmother had got a cold and was hoarse, answered:

'Tis your grandchild, Little Red Riding-Hood, who has brought you a custard and a little pot of butter mamma sends you.'

The Wolf cried out to her, softening his voice as much as he could:

'Pull the bobbin, and the latch will go up.'

Little Red Riding-Hood pulled the bobbin, and the door opened.

The Wolf, seeing her come in, said to her, hiding himself under the bed-clothes:

'Put the custard and the little pot of butter upon the stool, and come and lie down with me.'

Little Red Riding-Hood undressed herself and went into bed, where, being greatly amazed to see how her grandmother looked in her night-clothes, she said to her:

'Grandmamma, what great arms you have got!'

'That is the better to hug thee, my dear.'

'Grandmamma, what great legs you have got!'

'That is to run the better, my child.'

'Grandmamma, what great ears you have got!'

'That is to hear the better, my child.'

'Grandmamma, what great eyes you have got!'

'It is to see the better, my child.'

'Grandmamma, what great teeth you have got!'

'That is to eat thee up.'

And, saying these words, this wicked wolf fell upon Little Red Riding-Hood, and ate her all up.""",
    ),
    PublicDomainClassicEntry(
        title="The Story of the Three Little Pigs",
        source_author="Joseph Jacobs",
        source_url="https://en.wikisource.org/wiki/English_Fairy_Tales/The_Story_of_the_Three_Little_Pigs",
        source_origin_notes="Downloaded from Wikisource. Public-domain source text prepared for internal Buddybug Classics import.",
        source_text="""THERE was an old sow with three little pigs, and as she had not enough to keep them, she sent them out to seek their fortune.

The first that went off met a man with a bundle of straw, and said to him:

'Please, man, give me that straw to build me a house.'

Which the man did, and the little pig built a house with it. Presently came along a wolf, and knocked at the door, and said:

'Little pig, little pig, let me come in.'

To which the pig answered:

'No, no, by the hair of my chiny chin chin.'

The wolf then answered to that:

'Then I'll huff, and I'll puff, and I'll blow your house in.'

So he huffed, and he puffed, and he blew his house in, and ate up the little pig.

The second little pig met a man with a bundle of furze and said:

'Please, man, give me that furze to build a house.'

Which the man did, and the pig built his house. Then along came the wolf, and said:

'Little pig, little pig, let me come in.'

'No, no, by the hair of my chiny chin chin.'

'Then I'll puff, and I'll huff, and I'll blow your house in.'

So he huffed, and he puffed, and he puffed, and he huffed, and at last he blew the house down, and he ate up the little pig.

The third little pig met a man with a load of bricks, and said:

'Please, man, give me those bricks to build a house with.'

So the man gave him the bricks, and he built his house with them. So the wolf came, as he did to the other little pigs, and said:

'Little pig, little pig, let me come in.'

'No, no, by the hair on my chiny chin chin.'

'Then I'll huff, and I'll puff, and I'll blow your house in.'

Well, he huffed, and he puffed, and he huffed and he puffed, and he puffed and huffed; but he could not get the house down. When he found that he could not, with all his huffing and puffing, blow the house down, he said:

'Little pig, I know where there is a nice field of turnips.'

'Where?' said the little pig.

'Oh, in Mr. Smith's Home-field, and if you will be ready to-morrow morning I will call for you, and we will go together, and get some for dinner.'

'Very well,' said the little pig, 'I will be ready. What time do you mean to go?'

'Oh, at six o'clock.'

Well, the little pig got up at five, and got the turnips before the wolf came, who said:

'Little pig, are you ready?'

The little pig said: 'Ready! I have been and come back again, and got a nice potful for dinner.'

The wolf felt very angry at this, but thought that he would be up to the little pig somehow or other, so he said:

'Little pig, I know where there is a nice apple-tree.'

'Where?' said the pig.

'Down at Merry-garden,' replied the wolf, 'and if you will not deceive me I will come for you at five o'clock to-morrow and get some apples.'

Well, the little pig bustled up the next morning at four o'clock, and went off for the apples, hoping to get back before the wolf came; but he had further to go, and had to climb the tree, so that just as he was coming down from it, he saw the wolf coming. When the wolf came up he said:

'Little pig, what! are you here before me? Are they nice apples?'

'Yes, very,' said the little pig. 'I will throw you down one.'

And he threw it so far, that, while the wolf was gone to pick it up, the little pig jumped down and ran home.

The next day the wolf came again, and said to the little pig:

'Little pig, there is a fair at Shanklin this afternoon, will you go?'

'Oh yes,' said the pig, 'I will go; what time shall you be ready?'

'At three,' said the wolf. So the little pig went off before the time as usual, and got to the fair, and bought a butter-churn, which he was going home with, when he saw the wolf coming. Then he got into the churn to hide, and by so doing turned it round, and it rolled down the hill with the pig in it, which frightened the wolf so much, that he ran home without going to the fair.

He went to the little pig's house, and told him how frightened he had been by a great round thing which came down the hill past him. Then the little pig said:

'Hah, I frightened you, then. I had been to the fair and bought a butter-churn, and when I saw you, I got into it, and rolled down the hill.'

Then the wolf was very angry indeed, and declared he would eat up the little pig, and that he would get down the chimney after him. When the little pig saw what he was about, he hung on the pot full of water, and made up a blazing fire, and, just as the wolf was coming down, took off the cover, and in fell the wolf; so the little pig put on the cover again in an instant, boiled him up, and ate him for supper, and lived happy ever afterwards.""",
    ),
    PublicDomainClassicEntry(
        title="The Princess on the Pea",
        source_author="Hans Christian Andersen",
        source_url="https://en.wikisource.org/wiki/Fairy_Tales_and_Other_Stories_(Andersen,_Craigie)/The_Princess_on_the_Pea",
        source_origin_notes="Downloaded from Wikisource. Public-domain source text prepared for internal Buddybug Classics import.",
        source_text="""There was once a Prince who wanted to marry a princess; but she was to be a real princess. So he travelled about, all through the world, to find a real one, but everywhere there was something in the way. There were princesses enough, but whether they were real princesses he could not quite make out: there was always something that did not seem quite right. So he came home again, and was quite sad; for he wished so much to have a real princess.

One evening a terrible storm came on. It lightened and thundered, the rain streamed down; it was quite fearful! Then there was a knocking at the town-gate, and the old King went out to open it.

It was a Princess who stood outside the gate. But, mercy! how she looked, from the rain and the rough weather! The water ran down her hair and her clothes; it ran in at the points of her shoes, and out at the heels; and yet she declared that she was a real princess.

'Yes, we will soon find that out,' thought the old Queen. But she said nothing, only went into the bed-chamber, took all the bedding off, and put a pea on the bottom of the bedstead; then she took twenty mattresses and laid them upon the pea, and then twenty eider-down quilts upon the mattresses. On this the Princess had to lie all night. In the morning she was asked how she had slept.

'Oh, miserably!' said the Princess. 'I scarcely closed my eyes all night long. Goodness knows what was in my bed. I lay upon something hard, so that I am black and blue all over. It is quite dreadful!'

Now they saw that she was a real princess, for through the twenty mattresses and the twenty eider-down quilts she had felt the pea. No one but a real princess could be so tender-skinned.

So the Prince took her for his wife, for now he knew that he had a true princess; and the pea was put in the museum, and it is still to be seen there, unless somebody has carried it off.

Look you, this is a true story.""",
    ),
    PublicDomainClassicEntry(
        title="The Elves and the Shoemaker",
        source_author="Brothers Grimm (Alice Lucas translation)",
        source_url="https://en.wikisource.org/wiki/The_Fairy_Tales_of_the_Brothers_Grimm_(Rackham)/The_Elves_and_the_Shoemaker",
        source_origin_notes="Downloaded from Wikisource. Public-domain source text prepared for internal Buddybug Classics import.",
        source_text="""There was once a Shoemaker who, through no fault of his own, had become so poor that at last he had only leather enough left for one pair of shoes. At evening he cut out the shoes which he intended to begin upon the next morning, and since he had a good conscience, he lay down quietly, said his prayers, and fell asleep.

In the morning when he had said his prayers, and was preparing to sit down to work, he found the pair of shoes standing finished on his table. He was amazed, and could not understand it in the least.

He took the shoes in his hand to examine them more closely. They were so neatly sewn that not a stitch was out of place, and were as good as the work of a master-hand.

Soon after a purchaser came in, and as he was much pleased with the shoes, he paid more than the ordinary price for them, so that the Shoemaker was able to buy leather for two pairs of shoes with the money.

He cut them out in the evening, and next day, with fresh courage, was about to go to work; but he had no need to, for when he got up, the shoes were finished, and buyers were not lacking. These gave him so much money that he was able to buy leather for four pairs of shoes.

Early next morning he found the four pairs finished, and so it went on; what he cut out at evening was finished in the morning, so that he was soon again in comfortable circumstances, and became a well-to-do man.

Now it happened one evening, not long before Christmas, when he had cut out some shoes as usual, that he said to his Wife: 'How would it be if we were to sit up to-night to see who it is that lends us such a helping hand?'

The Wife agreed, lighted a candle, and they hid themselves in the corner of the room behind the clothes which were hanging there.

At midnight came two little naked men who sat down at the Shoemaker's table, took up the cut-out work, and began with their tiny fingers to stitch, sew, and hammer so neatly and quickly, that the Shoemaker could not believe his eyes. They did not stop till everything was quite finished, and stood complete on the table; then they ran swiftly away.

The next day the Wife said: 'The little men have made us rich, and we ought to show our gratitude. They were running about with nothing on, and must freeze with cold. Now I will make them little shirts, coats, waistcoats, and hose, and will even knit them a pair of stockings, and you shall make them each a pair of shoes.'

The Husband agreed, and at evening, when they had everything ready, they laid out the presents on the table, and hid themselves to see how the little men would behave.

At midnight they came skipping in, and were about to set to work; but, instead of the leather ready cut out, they found the charming little clothes.

At first they were surprised, then excessively delighted. With the greatest speed they put on and smoothed down the pretty clothes, singing:

'Now we're boys so fine and neat,
Why cobble more for other's feet?'

Then they hopped and danced about, and leapt over chairs and tables and out at the door. Henceforward, they came back no more, but the Shoemaker fared well as long as he lived, and had good luck in all his undertakings.""",
    ),
    PublicDomainClassicEntry(
        title="The Ugly Duckling",
        source_author="Hans Christian Andersen",
        source_url="https://en.wikisource.org/wiki/Hans_Andersen%27s_Fairy_Tales/The_Ugly_Duckling",
        source_origin_notes="Downloaded from Wikisource. Public-domain source text prepared for internal Buddybug Classics import.",
        source_text="""It was lovely summer weather in the country, and the golden corn, the green oats, and the haystacks piled up in the meadows looked beautiful. The stork walking about on his long red legs chattered in the Egyptian language, which he had learnt from his mother. The corn-fields and meadows were surrounded by large forests, in the midst of which were deep pools. It was, indeed, delightful to walk about in the country. In a sunny spot stood a pleasant old farm-house close by a deep river, and from the house down to the water side grew great burdock leaves, so high, that under the tallest of them a little child could stand upright. In this snug retreat sat a duck on her nest, watching for her young brood to hatch.

At length one shell cracked, and then another, and from each egg came a living creature that lifted its head and cried, 'Peep, peep.' At last the large egg broke, and a young one crept forth, crying, 'Peep, peep.' It was very large and ugly. The duck stared at it, and exclaimed, 'It is very large, and not at all like the others.'

On the next day the weather was delightful, and the mother duck took her young brood down to the water, and jumped in with a splash. One after another the little ducklings jumped in. The water closed over their heads, but they came up again in an instant, and swam about quite prettily. The ugly duckling was also in the water swimming with them.

'Oh,' said the mother, 'that is not a turkey; how well he uses his legs, and how upright he holds himself! He is my own child, and he is not so very ugly after all if you look at him properly.'

When they reached the farmyard, the poor duckling, who had crept out of his shell last of all, and looked so ugly, was bitten and pushed and made fun of, not only by the ducks, but by all the poultry. So it went on from day to day till it got worse and worse. The poor duckling was driven about by every one; even his brothers and sisters were unkind to him, and would say, 'Ah, you ugly creature, I wish the cat would get you,' and his mother said she wished he had never been born. So at last he ran away.

He came out on a large moor, inhabited by wild ducks. There he remained the whole night, feeling very tired and sorrowful. In the morning, when the wild ducks rose in the air, they stared at their new comrade. 'You are exceedingly ugly,' said the wild ducks, 'but that will not matter if you do not want to marry one of our family.'

The winter grew colder and colder. He was obliged to swim about on the water to keep it from freezing, but every night the space on which he swam became smaller and smaller. At length he became exhausted, and lay still and helpless, frozen fast in the ice.

Early in the morning, a peasant, who was passing by, saw what had happened. He broke the ice in pieces with his wooden shoe, and carried the duckling home to his wife. The warmth revived the poor little creature, but when the children wanted to play with him, the duckling thought they would do him some harm; so he started up in terror and escaped.

When the hard winter had passed, he found himself lying one morning in a moor amongst the rushes. He felt the warm sun shining, and saw that all around was beautiful spring. Then the young bird felt that his wings were strong, and he rose high into the air till he found himself in a large garden.

From a thicket close by came three beautiful white swans, rustling their feathers, and swimming lightly over the smooth water. The duckling remembered the lovely birds, and felt more strangely unhappy than ever.

'I will fly to those royal birds,' he exclaimed, 'and they will kill me, because I am so ugly, and dare to approach them; but it does not matter.'

Then he flew to the water, and swam towards the beautiful swans. The moment they espied the stranger, they rushed to meet him with outstretched wings.

'Kill me,' said the poor bird; and he bent his head down to the surface of the water, and awaited death.

But what did he see in the clear stream below? His own image; no longer a dark, gray bird, ugly and disagreeable to look at, but a graceful and beautiful swan.

He now felt glad at having suffered sorrow and trouble, because it enabled him to enjoy so much better all the pleasure and happiness around him. The great swans swam round the new-comer, and stroked his neck with their beaks, as a welcome.

Into the garden presently came some little children, and threw bread and cake into the water. They cried, 'There is another swan come; a new one has arrived.'

Then they threw more bread and cake into the water, and said, 'The new one is the most beautiful of all; he is so young and pretty.' And the old swans bowed their heads before him.

Then he felt quite ashamed, and hid his head under his wing; for he did not know what to do, he was so happy, and yet not at all proud. He had been persecuted and despised for his ugliness, and now he heard them say he was the most beautiful of all the birds. Then he rustled his feathers, curved his slender neck, and cried joyfully, from the depths of his heart, 'I never dreamed of such happiness as this, while I was an ugly duckling.'""",
    ),
]
